from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Category, Product
import sweetify
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Category
from .forms import *
from django.contrib import messages

from django.shortcuts import render
from django.db.models import Sum, Count, Prefetch
from sales.models import Sale, SaleDetail
@login_required(login_url="/accounts/login/")
def categories_list_view(request):
    if request.method == 'POST':
        form = CategoriesForm(request.POST) 
        if form.is_valid():
            form.save()
            messages.success(request, "Formulir Berhasil Dibuat")   
            return redirect('products:categories_list')
    else:
        form = CategoriesForm() 

    context = {
        'form': form,
        "breadcrumb": {"parent": "Kategori", "child": "Daftar Kategori"},
        "active_icon": "products_categories",
        "categories": Category.objects.all()
    }
    return render(request, "products/categories.html", context=context)


@login_required(login_url="/accounts/login/")
def categories_update_view(request, category_id):
    try:
        # Get the category to update
        category = Category.objects.get(id=category_id)
    except Exception as e:
        sweetify.success(
            request, 'There was an error trying to get the category!', extra_tags="danger")
        print(e)
        return redirect('products:categories_list')

    context = {
        "breadcrumb": {"parent": "Kategori", "child": "Edit Kategori"},
        "active_icon": "products_categories",
        "category_status": Category.status.field.choices,
        "category": category
    }

    if request.method == 'POST':
        try:
            # Save the POST arguments
            data = request.POST

            attributes = {
                "name": data['name'],
                "status": data['state'],
                "description": data['description']
            }

            # Check if a category with the same attributes exists
            if Category.objects.filter(**attributes).exists():
                sweetify.error(request, 'Category already exists!',
                               extra_tags="warning")
                return redirect('products:categories_add')

            # Get the category to update
            category = Category.objects.filter(
                id=category_id).update(**attributes)

            category = Category.objects.get(id=category_id)

            sweetify.success(request, '¡Category: ' + category.name +
                             ' updated successfully!', extra_tags="success")
            return redirect('products:categories_list')
        except Exception as e:
            sweetify.success(
                request, 'There was an error during the elimination!', extra_tags="danger")
            print(e)
            return redirect('products:categories_list')

    return render(request, "products/categories_update.html", context=context)


@login_required(login_url="/accounts/login/")
def categories_delete_view(request, category_id):
    """
    Args:
        request:
        category_id : The category's ID that will be deleted
    """
    try:
        # Get the category to delete
        category = Category.objects.get(id=category_id)
        category.delete()
        sweetify.success(request, '¡Category: ' + category.name +
                         ' deleted!', extra_tags="success")
        return redirect('products:categories_list')
    except Exception as e:
        sweetify.success(
            request, 'There was an error during the elimination!', extra_tags="danger")
        print(e)
        return redirect('products:categories_list')


@login_required(login_url="/accounts/login/")
def products_list_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST) 
        if form.is_valid():
            form.save()
            messages.success(request, "Formulir Berhasil Dibuat")   
            return redirect('products:products_list')
    else:
        form = ProductForm() 
    totals_per_product = (
        SaleDetail.objects
        .values('product__name')
        .annotate(total_qty=Sum('quantity'))
    )
    context = {
        'form': form,
        "breadcrumb": {"parent": "Barang", "child": "Daftar Barang"},
        'totals_per_product': totals_per_product,
        "active_icon": "products",
        "products": Product.objects.all().order_by('-id')
    }
    return render(request, "products/products.html", context=context)


@login_required(login_url="/accounts/login/")
def products_add_view(request):
    context = {
        "active_icon": "products_categories",
        "product_status": Product.status.field.choices,
        "categories": Category.objects.all().filter(status="ACTIVE")
    }

    if request.method == 'POST':
        # Save the POST arguments
        data = request.POST

        attributes = {
            "name": data['name'],
            "status": data['state'],
            "description": data['description'],
            "category": Category.objects.get(id=data['category']),
            "price": data['price']
        }

        # Check if a product with the same attributes exists
        if Product.objects.filter(**attributes).exists():
            sweetify.error(request, 'Product already exists!',
                           extra_tags="warning")
            return redirect('products:products_add')

        try:
            # Create the product
            new_product = Product.objects.create(**attributes)

            # If it doesn't exist, save it
            new_product.save()

            sweetify.success(request, 'Product: ' +
                             attributes["name"] + ' created successfully!', extra_tags="success")
            return redirect('products:products_list')
        except Exception as e:
            sweetify.success(
                request, 'There was an error during the creation!', extra_tags="danger")
            print(e)
            return redirect('products:products_add')

    return render(request, "products/products_add.html", context=context)


@login_required(login_url="/accounts/login/")
def products_update_view(request, product_id):

    # Get the product
    try:
        # Get the product to update
        product = Product.objects.get(id=product_id)
        
    except Exception as e:
        sweetify.success(
            request, 'There was an error trying to get the product!', extra_tags="danger")
        print(e)
        return redirect('products:products_list')

    context = {
        "active_icon": "products",
        "product_status": Product.status.field.choices,
        "product": product,
        "categories": Category.objects.all()
    }

    if request.method == 'POST':
        try:
            # Save the POST arguments
            data = request.POST

            attributes = {
                "name": data['name'],
                "status": data['state'],
                "description": data['description'],
                "category": Category.objects.get(id=data['category']),
                "price": data['price']
            }

            # Check if a product with the same attributes exists
            if Product.objects.filter(**attributes).exists():
                sweetify.error(request, 'Product already exists!',
                               extra_tags="warning")
                return redirect('products:products_add')

            # Get the product to update
            product = Product.objects.filter(
                id=product_id).update(**attributes)

            product = Product.objects.get(id=product_id)

            sweetify.success(request, '¡Product: ' + product.name +
                             ' updated successfully!', extra_tags="success")
            return redirect('products:products_list')
        except Exception as e:
            sweetify.success(
                request, 'There was an error during the update!', extra_tags="danger")
            print(e)
            return redirect('products:products_list')

    return render(request, "products/products_update.html", context=context)


@login_required(login_url="/accounts/login/")
def products_delete_view(request, product_id):
    Product.objects.get(id=product_id).delete()
    messages.success(request, "Data produk berhasil dihapus.")
    return redirect("products:products_list")    
    
def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@login_required(login_url="/accounts/login/")
def get_products_ajax_view(request):
    if request.method == 'POST':
        if is_ajax(request=request):
            data = []

            products = Product.objects.filter(
                name__icontains=request.POST['term'])
            for product in products[0:10]:
                item = product.to_json()
                data.append(item)

            return JsonResponse(data, safe=False)
