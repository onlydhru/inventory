from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import SignUpView, CustomLoginView,ProfileUpdateView, StockPDFView, UserListView, OrderHistoryPDFView, ExpiringProductsView, ProductListPDFView,  OrderSlipPDFView, LowStockAlertView, AnalyticsView, UserUpdateView, UserDeleteView, ProductCreateView, ProductListView, ProductUpdateView, StockListView, StockAddItemView, EditPriceView, StockDeleteView, SupplierDeleteView, SupplierListView, SupplierUpdateView, CreateOrderView, PurchaseOrderListView, PurchaseOrderUpdateView, OrderItemHistoryView, OrderItemView, OrderSlipView, MonthlySalesDataView, ProductDeleteView


urlpatterns = [
     path('', views.IndexView.as_view(), name='login'),
     path('signup/', SignUpView.as_view(), name='signup'),
     path('login/', CustomLoginView.as_view(), name='login'),
     path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
     path('adminbase/', views.AdminView.as_view(), name='adminbase'),
     path('dashboardpage/', views.DashboardView.as_view(), name='dashboardpage'),

     # User Urls
     path('users/', UserListView.as_view(), name='user_list'),
     path('users/update/<int:pk>/', views.UserUpdateView.as_view(), name='user_update'),
     path('users/delete/<int:pk>/', UserDeleteView.as_view(), name='delete_user'),
     path('profile/edit/', ProfileUpdateView.as_view(), name='edit_profile'),
     path('password/', auth_views.PasswordChangeView.as_view(template_name='change_password.html'), name='password_change'),
     path('password/done/', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),
     # Product Urls
     path('products/add/', ProductCreateView.as_view(), name='product_add'),
     path('products/', ProductListView.as_view(), name='product_list'),
     path('products/edit/<int:pk>/', ProductUpdateView.as_view(), name='product_edit'),
     path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
     path('products/pdf/', ProductListPDFView.as_view(), name='product_list_pdf'),
     # Stock Urls
     path('stocks/', StockListView.as_view(), name='stock_list'),
     path('stocks/add/', StockAddItemView.as_view(), name='stock_add_item'),
     path('stocks/edit/price/', views.EditPriceView.as_view(), name='edit_price'),
     path('stock_delete/<int:stock_id>/', StockDeleteView.as_view(), name='stock_delete'),
     path('stocks/pdf/', StockPDFView.as_view(), name='stock_list_pdf'),
     # Supplier Urls
     path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
     path('suppliers/edit/<int:pk>/', SupplierUpdateView.as_view(), name='supplier_edit'),
     path('suppliers/delete/<int:pk>/', views.SupplierDeleteView.as_view(), name='supplier_delete'),
     path('suppliers/add/', views.SupplierCreateView.as_view(), name='supplier_add'),
     path('create-order/', CreateOrderView.as_view(), name='create_order'),
     path('purchase-orders/', PurchaseOrderListView.as_view(), name='purchase_order_list'),
     path('purchase-orders/<int:pk>/update/', PurchaseOrderUpdateView.as_view(), name='purchase_order_update'),
     #Order Urls
     path('order_item_history/', views.OrderItemHistoryView.as_view(), name='order_item_history'),
     path('create-order', OrderItemView.as_view(), name='item_orders'),  # Must match redirect
     path('order-slip/<int:pk>/', OrderSlipView.as_view(), name='order_slip'),
     path('order/<int:pk>/', OrderSlipView.as_view(), name='order-slip'),
     path('order/<int:pk>/pdf/', OrderSlipPDFView.as_view(), name='order-slip-pdf'),
     path('order-history/pdf/', OrderHistoryPDFView.as_view(), name='order_history_pdf'),
     #Dashboard and Reports Urls
     path('monthly-sales-data/', MonthlySalesDataView.as_view(), name='monthly_sales_data'),
     path('expiring-products/', ExpiringProductsView.as_view(), name='expiring_products'),
     path('low-stock-alerts/', LowStockAlertView.as_view(), name='low_stock_alerts'),


]
if settings.DEBUG:
     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
