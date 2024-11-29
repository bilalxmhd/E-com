from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from core.forms import *
from django.contrib import messages
from core.models import *
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt



import razorpay
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_ID, settings.RAZORPAY_SECRET))

# Create your views here.
def index(request):
    products = Product.objects.all()
    return render(request, 'core/index.html',{'products':products})

def orderlist(request):
    if Order.objects.filter(user=request.user,ordered=False).exists():
        order = Order.objects.get(user=request.user,ordered=False)
        return render(request,'core/orderlist.html',{'order':order})
    return render(request,'core/orderlist.html',{'message':"Your Cart is Empty"})


def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST,request.FILES)
        if form.is_valid():
            print('True')
            form.save()
            print('Data saved successfully')
            messages.success(request,"product added successfully")
            return redirect('/')
        else:
            print("not working")
            messages.info(request,"Product is not added")

           
    else:
        form = ProductForm() 
    return render(request, 'core/add_product.html',{'form':form})

def product_desc(request,pk):
    product = Product.objects.get(pk=pk)
    return render(request, 'core/product_desc.html',{'product':product})


def add_to_cart(request,pk):
    #get the particular product of id = pk
    product = Product.objects.get(pk=pk)

    order_item, created = OrderItem.objects.get_or_create(
        product = product,
        user= request.user,
        ordered = False,
    )

    #get query set of order object of particular user
    order_qs = Order.objects.filter(user = request.user,ordered = False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk = pk).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request,"added quantity item")
            return redirect("product_desc",pk=pk)
        else:
            order.items.add(order_item)
            messages.info(request,"item added to cart")
            return redirect("product_desc",pk=pk)

    else:
        ordered_date = timezone.now()
        order =  Order.objects.create(user=request.user,ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request,"item added to cart")
        return redirect("product_desc",pk=pk)
 
def add_item(request,pk):
    product = Product.objects.get(pk=pk)

    order_item, created = OrderItem.objects.get_or_create(
        product = product,
        user= request.user,
        ordered = False,
    )

    #get query set of order object of particular user
    order_qs = Order.objects.filter(user = request.user,ordered = False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk = pk).exists():
            if order_item.quantity < product.product_available_count:
                order_item.quantity += 1
                order_item.save()
                messages.info(request,"added quantity item")
                return redirect("orderlist")
            else:
                messages.info(request,"Out of Stock")
                return redirect("orderlist")

        else:
            order.items.add(order_item)
            messages.info(request,"item added to cart")
            return redirect("product_desc",pk=pk)

    else:
        ordered_date = timezone.now()
        order =  Order.objects.create(user=request.user,ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request,"item added to cart")
        return redirect("product_desc",pk=pk)


def remove_item(request,pk):
    item = get_object_or_404(Product,pk= pk)
    order_qs = Order.objects.filter(
        user= request.user,
        ordered = False,
    )        
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(product__pk = pk).exists():
            order_item = OrderItem.objects.filter(
                product = item,
                user= request.user,
                ordered = False,
                )[0]
            if order_item.quantity >1:
                order_item.quantity -=1
                order_item.save()
            else:
                order_item.delete()
            messages.info(request,"item quantity was updated")
            return redirect("orderlist")        
        else:
            messages.info(request,"This item is not in your cart")
            return redirect("orderlist")
    else:
        messages.info(request,"You Do not have any order")
        return redirect("orderlist")    

def checkout_page(request):
    if checkoutAddress.objects.filter(user=request.user).exists():
        return render(request,'core/checkout_address.html',{'payment_allow':'allow'})
    if request.method =='POST':
        form = CheckoutForm(request.POST)
        try:
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip_code =form.cleaned_data.get('zip')

                checkout_address = checkoutAddress(
                    user = request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country = country,
                    zip_code = zip_code


                )
                checkout_address.save()
                print("It should render the summary page")
                return render(request,'core/checkout_address.html',{'payment_allow':'allow'})
        except Exception as e:
            messages.warning(request,"failed chekout")
            return redirect('checkout_page')
        
    else:
        form = CheckoutForm()
        return render(request,'core/checkout_address.html',{'form':form})



def payment(request):
    try:
        order = Order.objects.get(user=request.user, ordered =False)
        address = checkoutAddress.objects.get(user=request.user)
        order_amount = order.get_total_price()
        order_currency = "INR"
        order_receipt = order.order_id
        notes = {
            "street_address": address.street_address,
            "apartment_address": address.apartment_address,
            "country" : address.country.name,
            "zip" : address.zip_code,
        }
        razorpay_order = razorpay_client.order.create(
            dict(
                amount = order_amount*100,
                currency = order_currency,
                receipt =order_receipt,
                notes = notes,
                payment_capture = "0",
            )
        )
        print(razorpay_order["id"])
        order.razorpay_order_id = razorpay_order["id"]
        order.save()
        print("It should render the summary page")
        return render(
            request, "core/paymentrazorpay.html",
            {
                "order":order,
                "order_id":razorpay_order["id"],
                "orderId": order.order_id,
                "final_price": order_amount,
                "razorpay_merchant_id":settings.RAZORPAY_ID,

            },
        )
    except Order.DoesNotExist:
        print("oder not found")
        return HttpResponse("404 Error")
    
@csrf_exempt
def handlerequest(request):
    if request.method == "POST":
        try:
            payment_id = request.POST.get("razorpay_payment_id","")
            order_id = request.POST.get("razorpay_order_id","")
            signature = request.POST.get("razorpay_signature","")
            print(payment_id,order_id,signature)
            params_dict ={
                "razorpay_payment_id":payment_id,
                "razorpay_order_id":order_id,
                "razorpay_signature":signature,

            }
            try:
                order_db = Order.objects.get(razorpay_order_id = order_id)
                print("order found")
            except:
                print("order Not found")
                return HttpResponse("505 not found")
            order_db.razorpay_payment_id = payment_id
            order_db.razorpay_signature = signature
            order_db.save()
            print("working.....") 
            result = razorpay_client.utility.verify_payment_signature(params_dict)

 
            if result is None:
                print("working Finally.... ")
                amount = order_db.get_total_price()
                amount = amount * 100
                payment_status = razorpay_client.payment.capture(payment_id,amount)

                if payment_status is not None:
                    print(payment_status)
                    # Store items before clearing them
                    items_to_process = list(order_db.items.all())
                    
                    # Update product inventory
                    for item in items_to_process:
                        product = item.product
                        product.product_available_count -= item.quantity
                        product.save()
                    
                    # Mark order as complete
                    order_db.ordered = True
                    order_db.save()
                    
                    # Clear cart and delete items
                    OrderItem.objects.filter(user=order_db.user, ordered=False).delete()
                    order_db.items.clear()
                    
                    print("payment success")
                    request.session[
                        "order_complete"
                    ] = "Your Order is successfully placed, you will receive your order within 7 days"
                    messages.success(request, "Payment successful! Your order has been placed.")
                    return redirect("/")
                else:
                    print("payment failed")
                    order_db.ordered = False
                    order_db.save()
                    request.session[
                        "order_failed"
                    ] = "Unfortunately your order could not be placed, try again!"
                    return redirect("/")
            else:
                order_db.ordered = False
                order_db.save()
                return render(request, "core/paymentfailed.html")


        except:
            return redirect("/")
                   