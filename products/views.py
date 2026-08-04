from purchases.models import PurchaseDetail
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
from django.db.models import Sum, Count, Prefetch, Avg
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
        "categories": Category.objects.filter(owner=request.user).order_by('-id')  
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
    try:
        # Get the category to delete
        category = Category.objects.get(id=category_id, owner=request.user)
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
            form.instance.owner = request.user
            form.save()
            messages.success(request, "Formulir Berhasil Dibuat")   
            return redirect('products:products_list')
    else:
        form = ProductForm() 
    totals_per_product = (
        SaleDetail.objects
        .filter(product__owner=request.user)
        .values('product__name')
        .annotate(total_qty=Sum('quantity'))
    )
    context = {
        'form': form,
        "breadcrumb": {"parent": "Barang", "child": "Daftar Barang"},
        'totals_per_product': totals_per_product,
        "active_icon": "products",
        "products": Product.objects.filter(owner=request.user).order_by('-id')
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


def get_user_instance(user_input):
    from django.contrib.auth.models import User
    if isinstance(user_input, User):
        return user_input
    if hasattr(user_input, 'pk'):
        try:
            return User.objects.get(pk=user_input.pk)
        except Exception:
            pass
    try:
        return User.objects.get(pk=int(user_input))
    except Exception:
        return User.objects.first()


@login_required(login_url="/accounts/login/")
def get_products_ajax_view(request):
    current_user = get_user_instance(request.user)

    # Ambil parameter pencarian dari GET
    term = request.GET.get('term', '').strip()

    # Filter produk berdasarkan nama dan user
    products = Product.objects.filter(
        name__icontains=term, 
        owner=current_user, 
        status="ACTIVE"
    ).order_by('name')[:15]

    data = []
    for product in products:
        # Hitung stok & total
        total_masuk = SaleDetail.objects.filter(
            product=product, sale__owner=current_user
        ).aggregate(total=Sum('quantity'))['total'] or 0

        total_keluar = PurchaseDetail.objects.filter(
            product=product, purchase__owner=current_user
        ).aggregate(total=Sum('quantity'))['total'] or 0

        stock_qty = total_masuk - total_keluar
        price_fmt = f"{product.price:,.0f}".replace(",", ".")

        # Hitung rata-rata harga beli (dari SaleDetail = Barang Masuk)
        avg_buy = SaleDetail.objects.filter(
            product=product, sale__owner=current_user
        ).aggregate(avg=Avg('price'))['avg'] or 0

        last_detail = SaleDetail.objects.filter(
            product=product, sale__owner=current_user
        ).order_by('-id').first()
        last_price = float(last_detail.price) if last_detail else float(product.price)

        data.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'last_price': float(last_price),
            'stock_qty': float(stock_qty),
            'total_bought': float(total_masuk),
            'total_sold': float(total_keluar),
            'diff_qty': float(stock_qty),
            'avg_buy_price': float(avg_buy),
            # Text yang akan ditampilkan di dropdown
            'text': f"{product.name} — Rp {price_fmt} (Stok: {stock_qty} kg)"
        })

    # Return List JSON
    return JsonResponse(data, safe=False)
# def get_products_ajax_view(request):
#     if request.method == 'POST':
#         if is_ajax(request=request):
#             data = []
#             term = request.POST.get('term', '').strip()

#             products = Product.objects.filter(
#                 name__icontains=term, owner=request.user, status="ACTIVE"
#             ).order_by('name')

#             from purchases.models import PurchaseDetail

#             for product in products[0:15]:
#                 item = product.to_json()

#                 # Hitung Total Barang Masuk (Beli) dari SaleDetail
#                 total_masuk = SaleDetail.objects.filter(
#                     product=product, sale__owner=request.user
#                 ).aggregate(total=Sum('quantity'))['total'] or 0

#                 # Hitung Total Barang Keluar (Jual) dari PurchaseDetail
#                 total_keluar = PurchaseDetail.objects.filter(
#                     product=product, purchase__owner=request.user
#                 ).aggregate(total=Sum('quantity'))['total'] or 0

#                 # Stok Gudang = Barang Masuk - Barang Keluar
#                 stock_qty = total_masuk - total_keluar

#                 price_fmt = f"{product.price:,.0f}".replace(",", ".")

#                 item['price'] = product.price
#                 item['stock_qty'] = stock_qty
#                 item['total_bought'] = total_masuk
#                 item['total_sold'] = total_keluar
#                 item['diff_qty'] = stock_qty  # sama dengan stok gudang

#                 item['text'] = f"{product.name} — Rp {price_fmt} (Stok Gudang: {stock_qty} kg | Masuk: {total_masuk} kg | Keluar: {total_keluar} kg)"

#                 data.append(item)

#             return JsonResponse(data, safe=False)

