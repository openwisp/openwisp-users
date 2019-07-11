from django.core.exceptions import ValidationError
from rest_framework.generics import (ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView)
from rest_framework.response import Response

from .serializers import (OrganizationCreateUpdateSerializer,
                          OrganizationSerializer)


class BaseOrganizationListCreateAPIView(ListCreateAPIView):
    serializer_class = OrganizationSerializer

    def post(self, request, *args, **kwargs):
        options = {
            'description': request.POST.get('des', None),
            'name': request.POST.get('name', None),
            'slug': request.POST.get('slug', None),
            'email': request.POST.get('email', None),
            'url': request.POST.get('url', None)
        }
        org = self.org_model(**options)
        try:
            org.full_clean()
            org.save()
            org.add_user(request.user)
        except ValidationError as e:
            error = {
                'org_errors': str(e.messages)
            }
            return Response(data=error, status=400)
        success = {
            'org_success': 'Organization was successfully created'
        }
        return Response(data=success)

    def get_queryset(self):
        orgs = self.org_model.objects.filter(users=self.request.user)
        return orgs


class BaseOrganizationUpdateDeleteAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrganizationCreateUpdateSerializer
