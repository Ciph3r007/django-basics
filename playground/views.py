from django.shortcuts import render
from django.db import transaction, connection
from django.db.models import Q, F, Value, Func, Count, Avg, ExpressionWrapper
from django.db.models.fields import DecimalField
from django.db.models.functions import Concat
from django.contrib.contenttypes.models import ContentType
from store.models import Collection, Customer, Product, OrderItem, Order
from tags.models import TaggedItem

def say_hello(request):
    # price between 20 and 30 and inventory > 10
    query_set = Product.objects.filter(unit_price__range=(20, 30), inventory__gt=10)
    # price not between 20 and 30 and inventory > 10
    query_set = Product.objects.filter(~Q(unit_price__range=(20, 30)) | Q(inventory__gt=10))
    # inventory = collection_id
    query_set = Product.objects.filter(inventory=F('collection__id'))
    # sorting
    query_set = Product.objects\
                       .filter(unit_price__range=(20, 30), inventory__gt=10)\
                       .order_by('-unit_price', 'title')
    # sem shite
    query_set = Product.objects\
                       .filter(unit_price__range=(20, 30), inventory__gt=10)\
                       .order_by('unit_price', '-title').reverse()

    # select and limit
    query_set = Product.objects.all() # returns objects
    query_set = Product.objects.only('title')[5:10]  # returns objects (out of column access will result in multiple queries)
    query_set = Product.objects.values('title')[5:10] # returns dictionary ((out of column access will return null))
    query_set = Product.objects.values_list('title', 'unit_price')[5:10] # returns tuples (no column access, only values)
    query_set = Product.objects.defer('title')[5:10] # returns objects [inverse selection]

    # products that have been ordered
    query_set = Product.objects.filter(
        id__in=OrderItem.objects.values('product_id').distinct())\
            .order_by('title') # values_list is usable too

    # Joins
    # [for many to 1]
    query_set = Product.objects.select_related('collection')
    # [for many to many]
    query_set = Product.objects.prefetch_related('promotions')

    # last 5 orders with customer and items
    # should use 'orderitem_set' because of 1 to many relationship
    query_set = Order.objects.select_related('customer').order_by('-placed_at')[:5]\
                             .prefetch_related('orderitem_set__product')
    
    # annotated column
    query_set = Customer.objects.annotate(
        full_name=Func(F('first_name'), Value(' '), F('last_name'), function='CONCAT')
    )
    # SEM SHITE
    query_set = Customer.objects.annotate(
        full_name=Concat('first_name', Value(' '), 'last_name')
    )

    # aggregate functions
    # avg_price = Product.objects.aggregate(Avg('unit_price')) # Fetches instantly

    # orders of customers using group by
    # 1 to many relationship, but should use 'order' instead of 'order_set'
    # weird flex but ok!
    query_set = Customer.objects.annotate(
        order_count = Count('order')
    )

    # Expression Wrapper
    discounted_price = ExpressionWrapper(
        F('unit_price') * 0.8, output_field=DecimalField()
    )
    query_set = Product.objects.annotate(
        discounted_price=discounted_price
    )
    
    # generic relationships
    # content_type = ContentType.objects.get_for_model(Product) # Instant execution
    # query_set = TaggedItem.objects\
    #     .select_related('tag')\
    #     .filter(
    #         content_type=content_type,
    #         object_id=1
    #     )

    # using custom manager for generic relationship
    query_set = TaggedItem.objects.get_tags_for(Product, 1)

    # inserting record
    # collection = Collection()
    # collection.title = 'The Witcher 3'
    # collection.featured_product = Product(pk=1)
    # collection.save()  # Instant execution

    # updating record
    # collection = Collection.objects.get(pk=11)
    # collection.featured_product = None
    # collection.save()
    # # OR
    # Collection.objects.filter(pk=11).update(featured_product_id=None) # No intellisense

    # deleting record
    # Collection(pk=11).delete()
    # # deleting by filtering
    # Collection.objects.filter(pk__gte = 11).delete()

    # transactions
    # alternatively @transaction.atomic() decorator could have been used on the say_hello() function
    # with transaction.atomic():
    #     order = Order()
    #     order.customer_id = 1
    #     order.save()

    #     item = OrderItem()
    #     item.order = order
    #     item.product_id = 1
    #     item.quantity = 1
    #     item.unit_price = 10
    #     item.save()

    # raw sql query
    # for particular model
    query_set = Product.objects.raw('SELECT id, title, unit_price FROM store_product WHERE id < 10')
    # for the whole database
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM store_product WHERE id < 10')

    return render(request, 'hello.html', {'name': 'Pithibi', 'products':list(query_set)})
