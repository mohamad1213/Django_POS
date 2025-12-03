from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Customer
import sweetify
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt  # jangan pakai ini kecuali perlu
from django.shortcuts import render
from .forms import CustomerForm
import logging
logger = logging.getLogger(__name__)

@require_POST
def create_customer_ajax(request):
    logger.debug("AJAX create customer POST keys: %s", list(request.POST.keys()))
    form = CustomerForm(request.POST)
    if form.is_valid():
        customer = form.save()
        # label yang tampil di select — pakai first_name atau string representasi model
        label = getattr(customer, 'first_name', str(customer))
        return JsonResponse({'success': True, 'id': customer.id, 'label': label})
    else:
        logger.warning("CustomerForm errors: %s", form.errors)
        errors = {k: [str(m) for m in v] for k, v in form.errors.items()}
        return JsonResponse({'success': False, 'errors': errors}, status=400)

@login_required(login_url="/accounts/login/")
def customers_list_view(request):
    context = {
        "breadcrumb": {"parent": "pelanggan", "child": "Daftar Pelanggan"},
        "active_icon": "customers",
        "customers": Customer.objects.all()
    }
    return render(request, "customers/customers.html", context=context)


@login_required(login_url="/accounts/login/")
def customers_add_view(request):
    context = {
        "active_icon": "customers",
    }

    if request.method == 'POST':
        # Save the POST arguments
        data = request.POST

        attributes = {
            "first_name": data['first_name'],
            "last_name": data['last_name'],
            "address": data['address'],
            "email": data['email'],
            "phone": data['phone'],
        }

        # Check if a customer with the same attributes exists
        if Customer.objects.filter(**attributes).exists():
            sweetify.error(request, 'Customer already exists!',
                           extra_tags="warning")
            return redirect('customers:customers_add')

        try:
            # Create the customer
            new_customer = Customer.objects.create(**attributes)

            # If it doesn't exist save it
            new_customer.save()

            sweetify.success(request, 'Customer: ' + attributes["first_name"] + " " +
                             attributes["last_name"] + ' created successfully!', extra_tags="success")
            return redirect('customers:customers_list')
        except Exception as e:
            sweetify.success(
                request, 'There was an error during the creation!', extra_tags="danger")
            print(e)
            return redirect('customers:customers_add')

    return render(request, "customers/customers_add.html", context=context)


@login_required(login_url="/accounts/login/")
def customers_update_view(request, customer_id):
    """
    Args:
        request:
        customer_id : The customer's ID that will be updated
    """

    # Get the customer
    try:
        # Get the customer to update
        customer = Customer.objects.get(id=customer_id)
    except Exception as e:
        sweetify.success(
            request, 'There was an error trying to get the customer!', extra_tags="danger")
        print(e)
        return redirect('customers:customers_list')

    context = {
        "active_icon": "customers",
        "customer": customer,
    }

    if request.method == 'POST':
        try:
            # Save the POST arguments
            data = request.POST

            attributes = {
                "first_name": data['first_name'],
                "last_name": data['last_name'],
                "address": data['address'],
                "email": data['email'],
                "phone": data['phone'],
            }

            # Check if a customer with the same attributes exists
            if Customer.objects.filter(**attributes).exists():
                sweetify.error(request, 'Customer already exists!',
                               extra_tags="warning")
                return redirect('customers:customers_add')

            customer = Customer.objects.get(id=customer_id)

            sweetify.success(request, '¡Customer: ' + customer.get_full_name() +
                             ' updated successfully!', extra_tags="success")
            return redirect('customers:customers_list')
        except Exception as e:
            sweetify.success(
                request, 'There was an error during the update!', extra_tags="danger")
            print(e)
            return redirect('customers:customers_list')

    return render(request, "customers/customers_update.html", context=context)


@login_required(login_url="/accounts/login/")
def customers_delete_view(request, customer_id):
    """
    Args:
        request:
        customer_id : The customer's ID that will be deleted
    """
    try:
        # Get the customer to delete
        customer = Customer.objects.get(id=customer_id)
        customer.delete()
        sweetify.success(request, '¡Customer: ' + customer.get_full_name() +
                         ' deleted!', extra_tags="success")
        return redirect('customers:customers_list')
    except Exception as e:
        sweetify.success(
            request, 'There was an error during the elimination!', extra_tags="danger")
        print(e)
        return redirect('customers:customers_list')
