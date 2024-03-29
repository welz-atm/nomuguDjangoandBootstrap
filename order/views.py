from django.shortcuts import render, redirect, get_object_or_404
from .models import OrderItem, Order, Invoices
from django.db.models import Sum
from booking.calc_distance import calc_distance
from .forms import OrderItemForm, OrderCreateForm, PhotoForm
from .task import product_disapproved, order_picked, order_selected, send_text_for_order_picked
from authentication.decorators import merchant_required, shipper_required, shopper_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from product.models import Product
from django_countries import countries
import datetime
from django.http import JsonResponse
from django.core import serializers


@shopper_required()
def add_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    order_item = OrderItem.objects.create(product=product, user=request.user)
    orders = Order.objects.filter(user=request.user, ordered=False)
    if orders.exists():
        order = orders[0]
        if order.products.filter(product=product).exists():
            order_item.quantity += 1
            order_item.save()
            return redirect('my_cart')
        else:
            order.products.add(order_item)
            return redirect('my_cart')

    else:
        order = Order.objects.create(
            user=request.user)
        order.products.add(order_item)
        return redirect("my_cart")


@shopper_required()
def my_cart(request):
    try:
        orders = Order.objects.filter(user=request.user, ordered=False)
        order = orders[0]
    except Order.DoesNotExist:
        return render(request, 'no_cart.html', {})
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            created_form = form.save(commit=False)
            created_form.detail_created = True
            created_form.user = request.user
            order.products.update(address=created_form.address, city=created_form.city, state=created_form.state)
            order.save()
            order_items = order.products.all()
            for item in order_items:
                item.save()
            created_form.save()
            return redirect('my_cart')
    else:
        form = OrderCreateForm()

    context = {
        'order': order,
        'form': form,
        'countries': countries
    }
    return render(request, 'cart.html', context)


@shopper_required()
def edit_create_form(request, pk):
    order = Order.objects.get(pk=pk)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST, instance=order)
        if form.is_valid():
            created_form = form.save(commit=False)
            created_form.detail_created = True
            created_form.user = request.user
            order.products.update(address=created_form.address, city=created_form.city, state=created_form.state,
                                  country=created_form.country)
            order.save()
            order_items = order.products.all()
            for item in order_items:
                item.save()
            created_form.save()
            return redirect('my_cart')
    else:
        form = OrderCreateForm(instance=order)

    context = {
        'order': order,
        'form': form,
        'countries': countries
    }
    return render(request, 'edit_order_form.html', context)


@shopper_required()
def remove_from_cart(request, pk):
    ordered_item = get_object_or_404(OrderItem, pk=pk)
    ordered_item.delete()
    return redirect('my_cart')


@shopper_required()
def update_cart(request, pk):
    order = OrderItem.objects.get(pk=pk)
    if request.method == 'POST':
        form = OrderItemForm(request.POST, instance=order)
        if form.is_valid():
            updated_item = form.save(commit=False)
            updated_item.user = request.user
            updated_item.save()
            return redirect('my_cart')
    else:
        form = OrderItemForm(instance=order)
    context = {
        'form': form,
        'order': order
    }
    return render(request, 'update_cart.html', context)


@login_required()
def final_cart(request):
    order = Order.objects.get(user=request.user, ordered=False)
    context = {
        'order': order,
    }
    return render(request, 'invoice.html', context)


def cart_count(request):
    order_count = OrderItem.objects.filter(user=request.user).count()
    context = {
        'order_count': order_count
    }
    return render(request, 'cart.html', context)


@login_required()
def my_orders(request):
    if request.user.is_merchant:
        orders = OrderItem.objects.filter(product__merchant=request.user, ordered=True).order_by('-order_date').\
            select_related('user')
        if orders.exists():
            paginator = Paginator(orders, 10)
            page_number = request.GET.get('page')
            orders = paginator.get_page(page_number)
            context = {
                'orders': orders
            }
            return render(request, 'my_orders.html', context)
        else:
            return render(request, '404.html', {})
    elif request.user.is_shopper:
        orders = OrderItem.objects.filter(user=request.user, ordered=True).order_by('-order_date').select_related(
            'user')
        if orders.exists():
            paginator = Paginator(orders, 10)
            page_number = request.GET.get('page')
            orders = paginator.get_page(page_number)
            context = {
                'orders': orders
            }
            return render(request, 'my_orders.html', context)
        else:
            return render(request, '404.html')
    else:
        return render(request, 'unauthorized.html', {})


@login_required()
def delivered_orders(request):
    if request.user.is_shipper:
        orders = OrderItem.objects.filter(shipper=request.user, delivered=True).order_by('-order_date').select_related('user', 'product')
        if orders.exists():
            paginator = Paginator(orders, 10)
            page_number = request.GET.get('page')
            orders = paginator.get_page(page_number)
            context = {
                'orders': orders
            }
            return render(request, 'delivered_orders.html', context)
        else:
            return render(request, '404.html')
    else:
        return render(request, 'unauthorized.html', {})


@login_required()
def picked_up_orders(request):
    if request.user.is_shipper:
        orders = OrderItem.objects.filter(shipper=request.user, picked=True).order_by('-order_date').select_related('user', 'product')
        if orders.exists():
            paginator = Paginator(orders, 10)
            page_number = request.GET.get('page')
            orders = paginator.get_page(page_number)
            context = {
                'orders': orders
            }
            return render(request, 'picked_up_orders.html', context)
        else:
            return render(request, '404.html')
    else:
        return render(request, 'unauthorized.html', {})


@login_required()
def available_pickup(request):
    if request.user.is_shipper or request.user.is_admin or request.user.is_merchant:
        pick_ups = OrderItem.objects.filter(ordered=True, picked=False).order_by('-order_date').select_related('user',
                                                                                                               'product')
        if pick_ups.exists():
            paginator = Paginator(pick_ups, 10)
            page_number = request.GET.get('page')
            pick_ups = paginator.get_page(page_number)
            context = {
                'pick_ups': pick_ups
            }
            return render(request, 'available_pickup.html', context)
        else:
            return render(request, '404.html')
    else:
        return render(request, 'unauthorized.html', {})


@shipper_required()
def select_order_pickup(request, pk):
    order_item = get_object_or_404(OrderItem, pk=pk)
    if request.user.is_shipper:
        if order_item.picked is False:
            order_item.picked = True
            order_item.shipper = request.user
            order_item.save()
            order_selected.delay(request.user.pk, order_item.pk)
            return redirect('picked_up_order')
        else:
            messages.success(request, 'This order has been selected.')
            return redirect('available_pickup')
    else:
        return render(request, 'unauthorized.html', {})


@login_required()
def view_order(request, pk):
    order_item = OrderItem.objects.get(pk=pk)
    if request.user.is_shipper:
        context = {
            'order_item': order_item,
        }
        return render(request, 'view_order.html', context)
    elif request.user.is_shopper:
        context = {
            'order_item': order_item,
        }
        return render(request, 'view_order.html', context)
    else:
        return render(request, 'unauthorized.html', {})


@shipper_required()
def attach_picture(request, pk):
    order = OrderItem.objects.get(pk=pk)
    if request.user.is_shipper is True and request.user == order.shipper:
        if request.method == 'POST':
            form = PhotoForm(request.POST, request.FILES)
            if form.is_valid():
                picture = form.save()
                order.has_images = True
                order.image = picture
                order.save()
                return redirect('picked_up_order')
        else:
            form = PhotoForm()
        context = {
            'form': form
        }
        return render(request, 'attach_picture.html', context)
    else:
        return render(request, 'unauthorized.html', {})


@login_required()
def view_picture(request, pk):
    order = OrderItem.objects.get(pk=pk)
    context = {
        'order': order
    }
    return render(request, 'view_picture.html', context)


@shopper_required()
def confirm_picture(request, pk):
    order = OrderItem.objects.get(pk=pk)
    if request.user.is_shopper and order.user == request.user:
        if order.has_images is True:
            order.confirm_pickup = True
            order.save()
            return redirect('my_orders')
        else:
            messages.success(request, 'Needs you to confirm your order is same as desired')
            return redirect('my_orders')
    else:
        return render(request, 'unauthorized.html', {})


@shopper_required()
def disapprove_picture(request, pk):
    order = OrderItem.objects.get(pk=pk)
    if request.user.is_shopper and order.user == request.user:
        if order.has_images is True:
            order.confirm_pickup = False
            order.save()
            product_disapproved.delay(order.pk)
            return redirect('shopper_order')
    else:
        return render(request, 'unauthorized.html', {})


@shipper_required()
def pick_for_delivery(request, pk):
    order = OrderItem.objects.get(pk=pk)
    if request.user == order.shipper:
        if order.has_images is True and order.confirm_pickup is True:
            order.picked_for_delivery = True
            order.save()
            order_picked.delay(request.user.pk, order.pk)
            send_text_for_order_picked.delay(order.user.pk)
            return redirect('picked_up_order')
        else:
            messages.warning(request, 'Order has not been authorized by shopper')
            return redirect('picked_up_order')
    else:
        return render(request, 'unauthorized.html', {})


@shipper_required()
def product_delivered(request, pk):
    order_item = get_object_or_404(OrderItem, pk=pk)
    if order_item.shipper == request.user:
        order_item.delivered = True
        order_item.save()
        context = {
            'order_item': order_item
        }
        return render(request, 'pickup_order.html', context)
    else:
        return render(request, 'unauthorized.html', {})


@login_required()
def generate_invoice(request, pk):
    order = get_object_or_404(Order, pk=pk)
    invoice = Invoices.objects.create(owner=order.first_name, order=order)
    context = {
        'invoice': invoice
    }
    return render(request, 'invoice.html', context)


@login_required()
def invoice_list(request, pk):
    order = get_object_or_404(OrderItem, pk=pk)
    invoices = Invoices.objects.filter(order=order.product.merchant).select_related('owner', 'order')
    paginator = Paginator(invoices, 10)
    page_number = request.GET.get('page')
    invoices = paginator.get_page(page_number)
    context = {
        'invoices': invoices
    }

    return render(request, 'my_invoice_list.html', context)


@login_required()
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoices, pk=pk)
    if request.user == invoice.owner.user:
        context = {
            'invoice': invoice
        }
        return render(request, 'invoice_detail.html', context)
    elif request.user == invoice.order.product.merchant:
        context = {
            'invoice': invoice
        }
        return render(request, 'invoice_detail.html', context)
    else:
        return render(request, 'unauthorized.html', {})

