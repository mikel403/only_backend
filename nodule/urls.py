from django.urls import path, include
from rest_framework_nested import routers  
from . import views


router=routers.DefaultRouter()
# router.register("nodules",views.NoduleViewSet)
router.register("physicists",views.PhysicistViewSet)
router.register("descriptions",views.DescriptionmeViewSet, basename="descriptions")
router.register("nodules",views.NodulePhysicistViewSet, basename="nodules")
router.register("nodules-descriptions",views.NoduleDescriptionViewSet, basename="nodules-descriptions")
# router.register("nodules/<int:nodule_id>/description",views.DescriptionViewSet,basename="nodule-description")

nodules_router=routers.NestedDefaultRouter(router,"nodules",lookup="nodule")
nodules_router.register("descriptions",views.DescriptionViewSet,basename="nodule-description")
# nodules_router.register("AIdescription",views.AIDescription,basename="nodule-AIdescription")
urlpatterns = [
    path("", include(router.urls)),
    # path("nodules/<int:nodule_id>/description/",views.DescriptionViewSet.as_view),
    path("", include(nodules_router.urls)),
    path("<str:physicist__username>/nodules/<int:nodule_id>/descriptions",views.Description_detail),
    path("<str:AI_name>/descriptions",views.DescriptionAIViewSet),
    path("<str:physicist__username>/intercorrelation",views.Intercorrelation),
    path("intracorrelation",views.Intracorrelation),
    path("statistics",views.Statistics),
    path("<str:physicist__username>/statistics",views.Statistics_physician),
    path("nodules/<int:nodule_id>/AIDescription",views.AIDescription),
    path("nodules/<int:nodule_id>/expert-panel",views.AIExpertPanel),
    path("AIDetection",views.AIDetection),
    
    # path("", views.NoduleList.as_view()),
    # path("<int:pk>/", views.NoduleDetail.as_view()),
    # path("", views.NoduleDetail),
    
]