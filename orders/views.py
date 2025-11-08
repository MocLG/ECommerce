import json
import datetime
import stripe

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt


from cart.models import CartItem, Cart
from cart.views import _cart_id
from django.core.exceptions import ObjectDoesNotExist
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
from shop.models import Product


@login_required(login_url = 'accounts:login')
def payment_method(request):
    context = {
        'stripe_publishable_key': settings.STRIPE_PUBLIC_KEY
    }
    return render(request, 'shop/orders/payment_method.html', context)

@login_required(login_url = 'accounts:login')
def stripe_checkout(request, total=0, quantity=0):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    
    if cart_items.count() <= 0:
        return redirect('shop:shop')

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    
    tax = round(((17 * total)/100), 2)
    grand_total = total + tax
    handing = 15.00
    total = float(grand_total) + handing

    if request.method == 'POST':
        try:
            # Create a new order for this checkout
            order = Order()
            order.user = current_user
            order.order_total = total
            order.tax = tax
            order.ip = request.META.get('REMOTE_ADDR')
            order.save()

            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(order.id)
            order.order_number = order_number
            order.save()
            
            # Create Stripe checkout session with order metadata
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(total * 100),  # Stripe expects amount in cents
                        'product_data': {
                            'name': f'Order {order_number}',
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(
                    f"{reverse('orders:order_complete')}?order_number={order_number}&payment_id={{CHECKOUT_SESSION_ID}}"
                ),
                cancel_url=request.build_absolute_uri(reverse('orders:payment_cancel')),
                client_reference_id=current_user.id,
                metadata={'order_number': order_number},
            )
            # If request is JSON/ajax return session id for client-side redirect
            content_type = request.META.get('CONTENT_TYPE', '')
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
            if 'application/json' in content_type or is_ajax:
                return JsonResponse({'sessionId': checkout_session.id})
            # For normal form POST, redirect user directly to Stripe Checkout page
            return redirect(checkout_session.url)
        except Exception as e:
            # Return a proper HttpResponse with status code instead of a tuple
            return JsonResponse({'error': str(e)}, status=403)
    
    return redirect('shop:shop')


@login_required(login_url = 'accounts:login')
def checkout(request,total=0, total_price=0, quantity=0, cart_items=None):
    tax = 0.00
    handing = 0.00
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total_price += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        total = total_price + 10

    except ObjectDoesNotExist:
        pass # just ignore

    tax = round(((17 * total_price)/100), 2)  # BiH VAT rate of 17%
    grand_total = total_price + tax
    handing = 15.00
    total = float(grand_total) + handing
    
    context = {
        'total_price': total_price,
        'quantity': quantity,
        'cart_items': cart_items,
        'handing': handing,
        'vat': tax,
        'order_total': total,
    }
    return render(request, 'shop/orders/checkout/checkout.html', context)


@login_required(login_url = 'accounts:login')
def payment(request, total=0, quantity=0):
    current_user = request.user
    handing = 15.0
    # if the cart cout less than 0 , redirect to shop page 
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0 :
        return redirect('shop:shop')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = round(((17 * total)/100), 2)  # BiH VAT rate of 17%

    grand_total = total + tax
    handing = 15.00
    total = float(grand_total) + handing
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # shop all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address = form.cleaned_data['address']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") #20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()


            order = Order.objects.filter(
                user=current_user,
                is_ordered=False,
                order_number=order_number
            ).order_by('-id').first()
            
            if not order:
                messages.error(request, 'Order not found')
                return redirect('orders:checkout')
                
            context = {
                'order': order,
                'cart_items': cart_items,
                'handing': handing,
                'vat': tax,
                'order_total': total,
                'stripe_publishable_key': settings.STRIPE_PUBLIC_KEY,
            }
            return render(request, 'shop/orders/checkout/payment.html', context)
        else:
            messages.error(request, 'Your information not Vailed')
            return redirect('orders:checkout')
            
    else:
        return redirect('shop:shop')


def payments(request):
    body = json.loads(request.body)
    # Get the most recent pending order with this order number
    order = Order.objects.filter(
        user=request.user,
        is_ordered=False,
        order_number=body['orderID']
    ).order_by('-id').first()
    
    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)
    
    # Store transation details inside payment model 
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        status = body['status'],
        amount_paid = order.order_total,
    )
    
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()
    
    # Move the cart item to OrderProduct table 
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()
        
        # add variation to OrderProduct table
        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variation.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()

        
        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear Cart 
    CartItem.objects.filter(user=request.user).delete()

    # Send order received email to customer (only if not sent yet)
    try:
        if not order.email_sent:
            print(f"Preparing to send email for order {order.order_number}")
            # collect ordered products and subtotal for the email
            ordered_products = OrderProduct.objects.filter(order_id=order.id)
            ordered_products_data = []
            subtotall = 0
            for i in ordered_products:
                line_total = i.product_price * i.quantity
                ordered_products_data.append({
                    'product_name': i.product.name,
                    'unit_price': i.product_price,
                    'quantity': i.quantity,
                    'line_total': round(line_total, 2),
                })
                subtotall += line_total
            subtotal = round(subtotall, 2)

            print("Preparing email content...")
            subject = 'Thank you for your order!'
            try:
                message = render_to_string('shop/orders/checkout/payment_received_email.html', {
                    'user': request.user,
                    'order': order,
                    'ordered_products': ordered_products_data,
                    'subtotal': subtotal,
                    'handling': 15.00,
                })
            except Exception as template_error:
                print(f"Error rendering email template: {template_error}")
                raise

            to_email = order.email or request.user.email
            print(f"Sending email to: {to_email}")
            
            try:
                send_email = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [to_email])
                send_email.content_subtype = 'html'
                print("Attempting to send email...")
                send_email.send(fail_silently=False)
                print("Email sent successfully")
                
                order.email_sent = True
                order.save()
                print(f"Order {order.order_number} marked as email sent")
            except Exception as email_error:
                print(f"Error sending email: {str(email_error)}")
                if hasattr(email_error, 'smtp_error'):
                    print(f"SMTP error: {email_error.smtp_error}")
                raise
    except Exception as e:
        print(f"Error in email sending process: {str(e)}")
        if settings.DEBUG:
            print(f"Full error: {e.__class__.__name__}: {str(e)}")
        # Don't re-raise - we don't want to block order processing

    
    # Send order recieved email to cutomer 
    #subject = 'Thank you for your order!'
    #message = render_to_string('shop/orders/checkout/payment_recieved_email.html', {
    #    'user': request.user,
    #    'order':order,
    #})
    #to_email = request.user.email
    #send_email = EmailMessage(subject, message, to=[to_email])
    #send_email.send()
#
    #
    ## Send order recieved email to admin account 
    #subject = 'Thank you for your order!'
    #message = render_to_string('shop/orders/checkout/payment_recieved_email.html', {
    #    'user': request.user,
    #    'order':order,
    #})
    #to_email = request.user.email
    #send_email = EmailMessage(subject, message, to=['eshopsuppo@gmail.com'])
    #send_email.send()

    # Send order number and transation id back to sendDate method via JavaResponse
    data = {
            'order_number': order.order_number,
            'transID': payment.payment_id,
        }
    return JsonResponse(data)


@login_required(login_url = 'accounts:login')
def payment_success(request):
    session_id = request.GET.get('session_id', '')
    if session_id:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Get the existing order from session metadata
            order_number = session.get('metadata', {}).get('order_number')
            if not order_number:
                messages.error(request, 'Order information not found')
                return redirect('shop:shop')
                
            order = Order.objects.filter(
                order_number=order_number,
                is_ordered=False
            ).order_by('-id').first()
            
            if not order:
                messages.error(request, 'Order not found')
                return redirect('shop:shop')
            
            # Update order with payment info
            order.order_total = float(session.amount_total) / 100  # Convert back from cents
            order.tax = round((17 * float(session.amount_total / 100))/100, 2)  # BiH VAT rate of 17%
            order.ip = request.META.get('REMOTE_ADDR')
            
            # Create Payment record
            payment = Payment(
                user=request.user,
                payment_id=session.payment_intent,
                payment_method="Stripe",
                amount_paid=float(session.amount_total) / 100,
                status=session.payment_status,
            )
            payment.save()
            
            order.payment = payment
            order.is_ordered = True
            order.save()

            # Move CartItems to OrderProduct
            cart_items = CartItem.objects.filter(user=request.user)
            for item in cart_items:
                orderproduct = OrderProduct()
                orderproduct.order_id = order.id
                orderproduct.payment = payment
                orderproduct.user_id = request.user.id
                orderproduct.product_id = item.product_id
                orderproduct.quantity = item.quantity
                orderproduct.product_price = item.product.price
                orderproduct.ordered = True
                orderproduct.save()

                # Add variations
                cart_item = CartItem.objects.get(id=item.id)
                product_variation = cart_item.variation.all()
                orderproduct = OrderProduct.objects.get(id=orderproduct.id)
                orderproduct.variations.set(product_variation)
                orderproduct.save()

                # Reduce product stock
                product = Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()

            # Clear cart
            CartItem.objects.filter(user=request.user).delete()
            
            # For Stripe we rely on webhook to send the confirmation email.
            # Remove email send here to avoid duplicate emails; webhook will send and set `email_sent`.

            # Redirect to order completed page with order number and payment id
            return redirect(f"{reverse('orders:order_complete')}?order_number={order.order_number}&payment_id={payment.payment_id}")
    return redirect('shop:shop')

@login_required(login_url = 'accounts:login')
def payment_cancel(request):
    messages.error(request, 'Payment was cancelled')
    return redirect('orders:checkout')

def order_completed(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        # Get most recent completed order with this number
        order = Order.objects.filter(
            order_number=order_number,
            is_ordered=True
        ).order_by('-id').first()
        
        if not order:
            return redirect('shop:shop')
            
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotall = 0
        for i in ordered_products:
            subtotall += i.product_price * i.quantity
        subtotal = round(subtotall, 2)
        # If multiple Payment records exist with the same payment_id, pick the most recent one.
        payment = Payment.objects.filter(payment_id=transID).order_by('-id').first()
        if not payment:
            # If we can't find a payment, redirect to shop (or you may want to show an error page)
            return redirect('shop:shop')

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'shop/orders/order_completed/order_completed.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('shop:shop')
    

@csrf_exempt
def stripe_webhook(request):
    """Stripe webhook endpoint. Verifies signature and handles events.

    Attach this endpoint in the Stripe CLI or Stripe dashboard and set
    STRIPE_WEBHOOK_SECRET in your environment to the signing secret (whsec_...).
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Try to get order_number from session metadata (recommended) or skip
        order_number = session.get('metadata', {}).get('order_number')
        try:
            if order_number:
                # Get most recent pending order with this number
                order = Order.objects.filter(
                    order_number=order_number,
                    is_ordered=False
                ).order_by('-id').first()
                
                if not order:
                    # No matching order found, skip processing
                    return HttpResponse(status=200)

                # create payment record
                payment = Payment(
                    user=order.user,
                    payment_id=session.get('payment_intent') or session.get('id'),
                    payment_method='Stripe',
                    amount_paid=float(session.get('amount_total', 0)) / 100,
                    status='paid'
                )
                payment.save()

                order.payment = payment
                order.is_ordered = True
                order.save()

                # Move CartItems to OrderProduct and reduce stock (similar to payments())
                cart_items = CartItem.objects.filter(user=order.user)
                for item in cart_items:
                    orderproduct = OrderProduct()
                    orderproduct.order_id = order.id
                    orderproduct.payment = payment
                    orderproduct.user_id = order.user.id
                    orderproduct.product_id = item.product_id
                    orderproduct.quantity = item.quantity
                    orderproduct.product_price = item.product.price
                    orderproduct.ordered = True
                    orderproduct.save()

                    # add variation to OrderProduct table
                    cart_item = CartItem.objects.get(id=item.id)
                    product_variation = cart_item.variation.all()
                    orderproduct = OrderProduct.objects.get(id=orderproduct.id)
                    orderproduct.variations.set(product_variation)
                    orderproduct.save()

                    # Reduce the quantity of the sold products
                    product = Product.objects.get(id=item.product_id)
                    product.stock -= item.quantity
                    product.save()

                # Clear Cart
                CartItem.objects.filter(user=order.user).delete()

                # After processing the order, send confirmation email (if not already sent)
                try:
                    if not order.email_sent:
                        print(f"Webhook: Preparing to send email for order {order.order_number}")
                        ordered_products = OrderProduct.objects.filter(order_id=order.id)
                        ordered_products_data = []
                        subtotall = 0
                        for i in ordered_products:
                            line_total = i.product_price * i.quantity
                            ordered_products_data.append({
                                'product_name': i.product.name,
                                'unit_price': i.product_price,
                                'quantity': i.quantity,
                                'line_total': round(line_total, 2),
                            })
                            subtotall += line_total
                        subtotal = round(subtotall, 2)

                        print("Webhook: Preparing email content...")
                        subject = 'Thank you for your order!'
                        try:
                            message = render_to_string('shop/orders/checkout/payment_received_email.html', {
                                'user': order.user,
                                'order': order,
                                'ordered_products': ordered_products_data,
                                'subtotal': subtotal,
                                'handling': 15.00,
                            })
                        except Exception as template_error:
                            print(f"Webhook: Error rendering email template: {template_error}")
                            raise

                        to_email = order.email or order.user.email
                        print(f"Webhook: Sending email to: {to_email}")
                        
                        try:
                            send_email = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [to_email])
                            send_email.content_subtype = 'html'
                            print("Webhook: Attempting to send email...")
                            send_email.send(fail_silently=False)
                            print("Webhook: Email sent successfully")
                            
                            order.email_sent = True
                            order.save()
                            print(f"Webhook: Order {order.order_number} marked as email sent")
                        except Exception as email_error:
                            print(f"Webhook: Error sending email: {str(email_error)}")
                            if hasattr(email_error, 'smtp_error'):
                                print(f"Webhook: SMTP error: {email_error.smtp_error}")
                            raise
                except Exception as e:
                    print(f"Webhook: Error in email sending process: {str(e)}")
                    if settings.DEBUG:
                        print(f"Webhook: Full error: {e.__class__.__name__}: {str(e)}")
                    # Don't re-raise - we don't want to block webhook processing
        except Order.DoesNotExist:
            # If no order is found, we don't fail the webhook — just continue
            pass

    return HttpResponse(status=200)
