from django.shortcuts import get_object_or_404
from .models import MenuItem, Cart, Category, Order, OrderItem
from .serializers import MenuItemSerializer, UserSerializer, OrderSerializer
from .serializers import CategorySerializer, CartSerializer, OrderItemSerializer
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from .permissions import IsManager, IsDeliveryCrew
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user
from rest_framework import generics
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    search_fields = ['title', 'category__title']
    ordering_fields = ['price']
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsManager]
        
        return [permission() for permission in permission_classes]
    

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsManager]
        
        return [permission() for permission in permission_classes]



def user_group_management(request, group_name, pk=None):
    group = Group.objects.get(name=group_name)
    if request.method == 'POST':
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            group.user_set.add(user)
            return Response({"message": "Role assigned"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "error"}, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == "DELETE":
        user = get_object_or_404(User, pk=pk)
        group.user_set.remove(user)
        return Response({"message": "Role removed"}, status=status.HTTP_200_OK)

    users = group.user_set.all()
    user_serializer = UserSerializer(users, many=True)
    return Response(user_serializer.data, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([IsManager])
def roles(request, role):
    if role == "manager":
        return user_group_management(request, 'Manager')
    elif role == "delivery-crew":
        return user_group_management(request, 'Delivery Crew')
    else: 
        return Response({"message": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsManager])
def remove_role(request, role, pk):
    if role == "manager":
        return user_group_management(request, 'Manager', pk)
    elif role == "delivery-crew":
        return user_group_management(request, 'Delivery Crew', pk)
    else: 
        return Response({"message": "Bad request"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart(request):
    if request.method == "POST":
        serialized_data = CartSerializer(data=request.data)
        serialized_data.is_valid()
        id = serialized_data.data.get('menuitem_id')
        quantity =  serialized_data.data.get('quantity')
        item = get_object_or_404(MenuItem, pk=id)
        price = int(quantity) * item.price
        try:
            Cart.objects.create(user=request.user, menuitem_id=id, quantity=quantity, unit_price=item.price, price=price)
            return Response({"message": "Item added to cart"})
        except Exception as e:
            print(e)
            return Response({"message": "error"})
    elif request.method == "DELETE":
        user_cart = Cart.objects.filter(user=request.user)
        user_cart.delete()
        return Response({"message": "Items deleted"}, status=status.HTTP_200_OK)

    cart = Cart.objects.filter(user=request.user)
    cart_serializer = CartSerializer(cart, many=True)
    return Response(cart_serializer.data)

class OrderView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.groups.filter(user='Manager'):
            return Order.objects.all()
        elif self.request.user.groups.count()==0: #normal customer - no group
            return Order.objects.all().filter(user=self.request.user)
        elif self.request.user.groups.filter(name='Delivery Crew').exists(): #delivery crew
            return Order.objects.all().filter(delivery_crew=self.request.user)  #only show oreders assigned to him
        else: #delivery crew or Manager
            return Order.objects.all()

    def create(self, request, *args, **kwargs):
        menuitem_count = Cart.objects.all().filter(user=self.request.user).count()
        if menuitem_count == 0:
            return Response({"message:": "no item in cart"})

        data = request.data.copy()
        total = self.get_total_price(self.request.user)
        data['total'] = total
        data['user'] = self.request.user.id
        order_serializer = OrderSerializer(data=data)
        if (order_serializer.is_valid()):
            order = order_serializer.save()

            items = Cart.objects.all().filter(user=self.request.user).all()

            for item in items.values():
                orderitem = OrderItem(
                    order=order,
                    menuitem_id=item['menuitem_id'],
                    unit_price=item['unit_price'],
                    price=item['price'],
                    quantity=item['quantity'],
                )
                orderitem.save()

            Cart.objects.all().filter(user=self.request.user).delete() #Delete cart items

            result = order_serializer.data.copy()
            result['total'] = total
            return Response(order_serializer.data)
        else:
            return Response({'message': "error"}, status.HTTP_400_BAD_REQUEST)
    
    def get_total_price(self, user):
        total = 0
        items = Cart.objects.all().filter(user=user).all()
        for item in items.values():
            total += item['price']
        return total


class SingleOrderView(generics.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        if self.request.user.groups.count()==0: # Normal user, not belonging to any group = Customer
            return Response('Not Ok')
        else: #everyone else - Super Admin, Manager and Delivery Crew
            return super().update(request, *args, **kwargs)
