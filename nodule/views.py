from django.shortcuts import get_object_or_404
from django.db.models import Value, BooleanField, Count, Q, Func
from django.http import FileResponse, Http404
from django.contrib.contenttypes.models import ContentType
from django.db.models import OuterRef,Subquery
from django.contrib.auth import get_user_model
# from django.contrib.contenttypes.prefetch import GenericPrefetch

from rest_framework.decorators import api_view, action,permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
# from rest_framework.views import APIView
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.exceptions import NotFound, PermissionDenied
from nodule.utils.YOLO import convertImageCV, yoloCrop
from nodule.utils.descriptionModel import results_simple

from nodule.utils.statistics import statistics_fn

from . import models
from . import serializers

from .utils.correlation import intercorrelation_Fleiss_fn, intercorrelation_fn, intracorrelation_fn
from .utils.expert_panel import expertPanel_fn
from .utils.AIDescriptionFromDatabase import isInDatabase,probs_database

import random
# Create your views here.


# @api_view(['GET', 'POST'])
# def NoduleDetail(request):
#     if request.method == 'GET':
#         queryset = Nodule.objects.all()
#         serializer = NoduleSerializer(
#             queryset, many=True, context={'request': request})
#         return Response(serializer.data)
#     elif request.method == 'POST':
#         serializer = NoduleSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
User = get_user_model()
def get_content_type(user_id):
    content_type_model = None
    if models.Physicist.objects.filter(user_id=user_id).exists():
        content_type_model = models.Physicist
    elif models.AI.objects.filter(id=user_id).exists():
        content_type_model = models.AI
    elif models.TestUser.objects.filter(user_id=user_id).exists():

        content_type_model = models.TestUser
    
    elif User.objects.filter(id=user_id).exists():
        content_type_model = User
    else:
        raise ValueError("El tipo de usuario no es válido.")
    content_type_id = ContentType.objects.get_for_model(content_type_model).id
    return content_type_id

    
@permission_classes([IsAuthenticated])    
class DescriptionViewSet(ListModelMixin, CreateModelMixin,GenericViewSet):
    serializer_class=serializers.DescriptionSerializer
    def get_serializer_context(self):
        nodule_id = self.kwargs["nodule_pk"]

        # Obtener el user_id del usuario autenticado
        
        context = super().get_serializer_context()
        context["nodule_id"] = self.kwargs["nodule_pk"]
        return context
    
    def get_queryset(self):
        
        return models.Description.objects.filter(nodule_id=self.kwargs["nodule_pk"],user=self.request.user).select_related("user","ai")
    
#We are going to create a view for an url that takes the last description of a nodule given by a physicist. This physicist will appear as first name in this url.
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def Description_detail(request,nodule_id,physicist__username):
    # description=get_object_or_404(models.Description.objects, nodule_id=nodule_id, physicist__user__first_name=physicist__first_name,)
    description=models.Description.objects.filter(nodule_id=nodule_id,user__username=physicist__username,user__physicist__isnull=False).select_related("user").last()
    if description:
        serializer=serializers.DescriptionSerializer(description,many=False)
    else:
        raise Http404()
    return Response(serializer.data)

    


    


#We generate a view to obtain all descriptions given by the physicist
@permission_classes([IsAuthenticated])
class DescriptionmeViewSet(ListModelMixin,GenericViewSet):
    serializer_class=serializers.DescriptionSerializer
    # def get_queryset(self):
    #     return Nodule.objects.all()
    
    def get_serializer_context(self):
        return {"request":self.request}
    def get_queryset(self):
        return models.Description.objects.filter(user=self.request.user).select_related("user")
    
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def DescriptionAIViewSet(request,AI_name):
    description=models.Description.objects.filter(ai__name=AI_name)
    serializer=serializers.DescriptionSerializer(description,many=True)
    return Response(serializer.data)
        
@permission_classes([IsAuthenticated])    
class PhysicistViewSet(CreateModelMixin, RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    queryset=models.Physicist.objects.all()
    serializer_class=serializers.PhysicistSerializer
    def get_serializer_context(self):
        return {"user_id":self.request.user.id}

    @action(detail=False,methods=["GET","PUT"])
    def me(self,request):
        physicist=get_object_or_404(models.Physicist,user_id=request.user.id)
        if request.method=="GET":
            serializer=serializers.PhysicistSerializer(physicist)
            return Response(serializer.data)
        elif request.method=="PUT":
            serializer=serializers.PhysicistSerializer(physicist,data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

# class NoduleViewSet(ModelViewSet):
#     queryset=models.Nodule.objects.all()
#     serializer_class=serializers.NoduleSerializer

#     def get_serializer_context(self):
#         return {"request":self.request}

@permission_classes([IsAuthenticated])
class NodulePhysicistViewSet(ListModelMixin,CreateModelMixin,GenericViewSet):
    seed = 42
    random.seed(seed)   
    serializer_class=serializers.NodulePhysicistSerializer
    def get_serializer_context(self):
        return {"new":self.request.user.username}
    def get_queryset(self):
        user = self.request.user
        limit=self.request.GET.get("_limit")
        init=self.request.GET.get("_start")
        name=self.request.GET.get("_name")
        timesDescribed=self.request.GET.get("_timesDescribed")
        yourData=self.request.GET.get("_yourData")

        user_id=self.request.user.id
        content_type_id=get_content_type(user_id)
        described=models.Nodule.objects.prefetch_related("descriptions").filter(descriptions__user=self.request.user)
        

        if name:
            described=described.filter(name__contains=name)
        
        if yourData=="true":
            described=described.filter(new=self.request.user.username)
        else:
            described=described.filter(Q(new=self.request.user.username) | Q(new__isnull=True))

        described=described.annotate(numDescriptions=Count("descriptions"))
        
        if timesDescribed:
            if timesDescribed=="1":
                described=described.filter(numDescriptions=timesDescribed)
            elif timesDescribed=="2":
                described=described.filter(numDescriptions__gt=1)
            
        numNodules2Times=Value(described.filter(numDescriptions__gt=1).count())
        numNodulesDescribed=Value(described.count())
        if timesDescribed and (timesDescribed!="0" and timesDescribed!="all"):
            numNodules=Value(0)
            if limit:
                limit=int(limit)
                init=int(init)
                described=described[init:init+limit]
            return described.annotate(numNodules=numNodules,numNodules2Times=numNodules2Times,numNodulesDescribed=numNodulesDescribed)
            
        
        notDescribed=models.Nodule.objects.prefetch_related("descriptions").exclude(descriptions__user=user)
        if name:
            notDescribed=notDescribed.filter(name__contains=name)
        if yourData=="true":
            notDescribed=notDescribed.filter(new=self.request.user.username)
        else:
            notDescribed=notDescribed.filter(Q(new=self.request.user.username) | Q(new__isnull=True))

        numNodules=Value(notDescribed.count())
        notDescribed=notDescribed.annotate(numDescriptions=Value(0))
        
        
        
        # described=models.Nodule.objects.prefetch_related("descriptions").filter(descriptions__physicist_id=self.request.user.id).annotate(isdescribed=Value(True))
        
        if timesDescribed and timesDescribed=="0":
            numNodules2Times=Value(0)
            numNodulesDescribed=Value(0)
            if limit:
                limit=int(limit)
                init=int(init)
                notDescribed=notDescribed[init:init+limit]
            return notDescribed.annotate(numNodules=numNodules,numNodules2Times=numNodules2Times,numNodulesDescribed=numNodulesDescribed)
        
        
        described=described.annotate(numNodules=numNodules,numNodules2Times=numNodules2Times,numNodulesDescribed=numNodulesDescribed)
        notDescribed=notDescribed.annotate(numNodules=numNodules,numNodules2Times=numNodules2Times,numNodulesDescribed=numNodulesDescribed)
        combination = notDescribed.union(described)
        if limit:
            limit=int(limit)
            init=int(init)
            combination=combination[init:init+limit]
        
        # def list(self,request,*args,**kwargs):
        #     param=request.Get.get("param")
        #     print(param)
        return combination
    

@permission_classes([IsAuthenticated])
class NoduleDescriptionViewSet(ListModelMixin,GenericViewSet):
    serializer_class=serializers.NoduleDescriptionsSerializer
    def get_serializer_context(self):
        return {"request":self.request}
    def get_queryset(self):
        user=self.request.user
        limit=self.request.GET.get("_limit")
        init=self.request.GET.get("_start")
        name=self.request.GET.get("_name")
        timesDescribed=self.request.GET.get("_timesDescribed")
        yourData=self.request.GET.get("_yourData")
        described=models.Nodule.objects.prefetch_related("descriptions").filter(descriptions__user=user)

        if name:
            described=described.filter(name__contains=name)
        
        if yourData=="true":
            described=described.filter(new=self.request.user.username)
        else:
            described=described.filter(Q(new=self.request.user.username) | Q(new__isnull=True))
        
        described=described.annotate(numDescriptions=Count("descriptions"))
        if timesDescribed:
            if timesDescribed=="1":
                described=described.filter(numDescriptions=timesDescribed)
            elif timesDescribed=="2":
                described=described.filter(numDescriptions__gt=1)
            
        numNodules2Times=Value(described.filter(numDescriptions__gt=1).count())
        numNodulesDescribed=Value(described.count())
        if limit:
            limit=int(limit)
            init=int(init)
            described=described[init:init+limit]
        return described.annotate(numNodules2Times=numNodules2Times,numNodulesDescribed=numNodulesDescribed)
            
        
        
        
        # filtered_descriptions_subquery = models.Nodule.objects.prefetch_related("descriptions").filter(
        # descriptions__physicist_id=self.request.user.id
        # ).values("id","name", "image","new",'descriptions__birads',"descriptions__physicist_id")




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def AIDetection(request):
    if "image" in request.FILES:
        image=request.FILES["image"]
        image=convertImageCV(image)
        boxes=yoloCrop(image)
    return Response(boxes)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def AIDescription(request, nodule_id):
    # Get or create the nodule instance
    nodule, created = models.Nodule.objects.get_or_create(id=nodule_id)    
    # Get the actual file path of the image
    print(nodule.name)
    if isInDatabase(nodule.name):
        print(nodule.name)
        probs=probs_database(nodule.name)
    else:
        image_path = nodule.image.path if nodule.image else None

        if image_path is None:
            return Response({"error": "No image available for this nodule"}, status=400)


        # Process the image (results_simple is a custom function assumed to exist)
        _, words,probs = results_simple(image_path)
        # Construct the response
        # result = {
        #     "shape": words[0],
        #     "margin": words[1],
        #     "orientation": words[2],
        #     "echogenicity": words[3],
        #     "posterior": words[4],
        #     "calcification": None,
        #     "suggestivity": words[5],
        #     "birads": words[6],
        # }

    return Response(probs)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def Intercorrelation(request,physicist__username):
    user=request.user
    
    # prefetch=GenericPrefetch("content_object",[models.Physicist.object.all()])
    descriptions=models.Description.objects.select_related("user").filter(user=user)
    desc_serializer=serializers.DescriptionSerializer(descriptions,many=True)
    descriptions_other=models.Description.objects.select_related("user").filter(user__username=physicist__username)
    desc_other_serializer=serializers.DescriptionSerializer(descriptions_other,many=True)
    if len(desc_other_serializer.data) == 0:
        return Response({"error": "Physician not found"}, status=status.HTTP_404_NOT_FOUND)
    result=intercorrelation_fn(desc_serializer.data,desc_other_serializer.data)
    return Response(result)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def Intercorrelation_Fleiss(request):
    user=request.user
    
    # prefetch=GenericPrefetch("content_object",[models.Physicist.object.all()])
    descriptions=models.Description.objects.select_related("user").filter(user=user)
    desc_serializer=serializers.DescriptionSerializer(descriptions,many=True)
    
    #For the Fleiss kappa we only consider physicians
    descriptions_other=models.Description.objects.select_related("user").exclude(user=user).filter(user__physicist__isnull=False)
    desc_other_serializer=serializers.DescriptionSerializer(descriptions_other,many=True)

    result = intercorrelation_Fleiss_fn(desc_serializer.data, desc_other_serializer.data, user_id=request.user.id)
    return Response(result)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def Intracorrelation(request):
    user=request.user
    
    descriptions=models.Description.objects.select_related("user").filter(user=user)
    desc_serializer=serializers.DescriptionSerializer(descriptions,many=True)
    result=intracorrelation_fn(desc_serializer.data)
    return Response(result)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def Statistics(request):
    user=request.user
    
    descriptions=models.Description.objects.select_related("user").filter(user=user)
    desc_serializer=serializers.DescriptionSerializer(descriptions,many=True)
    result=statistics_fn(desc_serializer.data)
    return Response(result)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def Statistics_physician(request,physicist__username):
    user=request.user
    if physicist__username=="Overall":
        descriptions=models.Description.objects.select_related("user").filter(user__physicist__isnull=False).exclude(user=user)
        physicians=models.Physicist.objects.exclude(user=user).count()
        
    else:
        descriptions=models.Description.objects.select_related("user").filter(user__username=physicist__username)
        physicians=1
    desc_serializer=serializers.DescriptionSerializer(descriptions,many=True)
    result=statistics_fn(desc_serializer.data)
    result["physicians"]=physicians
    return Response(result)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def AIExpertPanel(request,nodule_id):
    user=request.user
    #Cogemos todas las descripciones que no pertenezcan a la radióloga, pero que sean de otros radiólogos
    descriptions_other=models.Description.objects.select_related("user").select_related("nodule").filter(nodule_id=nodule_id).filter(user__physicist__isnull=False).exclude(user=user)
    desc_serializer=serializers.DescriptionSerializer(descriptions_other,many=True)
    result=expertPanel_fn(desc_serializer.data)
    return Response(result)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def physician_ground_truth(request,nodule_id,physicist__username):
    user=request.user
    physician = User.objects.filter(username=physicist__username).first()
    if not physician:
        raise NotFound(detail="physician_not_found")
    #Cogemos las descripciones del usuario
    descriptions = models.Description.objects.select_related("user", "nodule").filter(
        nodule_id=nodule_id,
        user=physician,
    )
    if not descriptions.exists():
        raise NotFound(detail="description_not_found")
    desc_serializer=serializers.DescriptionSerializer(descriptions,many=True)
    result=expertPanel_fn(desc_serializer.data)
    return Response(result)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def private_nodule_image(request, pk, which="image"):
    nodule = models.Nodule.objects.get(pk=pk)
    f = nodule.image if which == "image" else nodule.full_image
    if not f:
        raise Http404
    is_owner = (nodule.new == request.user.username)
    is_public_dataset = (nodule.new is None)
    if not (is_public_dataset or is_owner or request.user.is_staff):
        raise PermissionDenied("You are not authorized to access this image.")

    return FileResponse(f.open("rb"))
# def NodulePhysicistViewSet(request):
#     notDescribed=models.Nodule.objects.prefetch_related("descriptions").exclude(descriptions__physicist_id=self.request.user.id).annotate(isdescribed=Value(False))
#     described=models.Nodule.objects.prefetch_related("descriptions").filter(descriptions__physicist_id=self.request.user.id).annotate(isdescribed=Value(True))
#     combination = notDescribed.union(described)
#     serializer = serializers.NodulePhysicistSerializer(
#             combination, many=True, context={"request":request})
#     return Response(serializer.data)

    # def get_queryset(self):
    #     return Nodule.objects.all()
    
    # def get_serializer_class(self):
    #     return NoduleSerializer
    
    # def get_serializer_context(self):
    #     return {"request":self.request}
    
# class NoduleList(ListCreateAPIView):
#     queryset=Nodule.objects.all()
#     serializer_class=NoduleSerializer
#     # def get_queryset(self):
#     #     return Nodule.objects.all()
    
#     # def get_serializer_class(self):
#     #     return NoduleSerializer
    
#     def get_serializer_context(self):
#         return {"request":self.request}
    
# class NoduleDetail(RetrieveUpdateDestroyAPIView):
#     queryset=Nodule.objects.all()
#     serializer_class=NoduleSerializer
    

   



# # class NoduleDetail(APIView):
# #     # queryset=Nodule.objects.all()
# #     # def get_queryset(self):
# #     #     return Nodule.objects.all()
    
# #     # def get_serializer_class(self):
# #     #     return NoduleSerializer
    
# #     # def get_serializer_context(self):
# #     #     return {"request":self.request}
# #     def get(self,request):
# #         queryset = Nodule.objects.all()
# #         serializer = NoduleSerializer(
# #             queryset, many=True, context={'request': request})
# #         return Response(serializer.data)

# #     def post(self,request):
# #         serializer=NoduleSerializer(data=request.data)
# #         serializer.is_valid(raise_exception=True)
# #         serializer.validated_data
# #         serializer.save()
# #         return Response(serializer, status=status.HTTP_201_CREATED)


