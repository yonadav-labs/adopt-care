import datetime

from django.db.models import Sum, Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.pagination import PageNumberPagination

from ..models import BilledActivity, BillingType
from ..permissions import IsAdminOrEmployeeActivityOwner
from .serializers import BilledActivitySerializer, BillingTypeSerializer
from apps.core.api.mixins import ParentViewSetPermissionMixin
from apps.core.api.views import OrganizationViewSet
from apps.core.models import Organization
from apps.patients.models import PatientProfile
from apps.tasks.permissions import IsEmployeeOrPatientReadOnly


class BilledActivityPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 20


class BilledActivityViewSet(viewsets.ModelViewSet):
    """
    Viewset for :model:`billings.BilledActivity`
    ========

    create:
        Creates :model:`billings.BilledActivity` object.
        Only admins and employees are allowed to perform this action.

    update:
        Updates :model:`billings.BilledActivity` object.
        Only admins and employee owners are allowed to perform this action.

    partial_update:
        Updates one or more fields of an existing billed activity object.
        Only admins and employee owners are allowed to perform this action.

    retrieve:
        Retrieves a :model:`billings.BilledActivity` instance.
        Admins and employee members will have access to billed activities that
        belong to the care team.

    list:
        Returns list of all :model:`billings.BilledActivity` objects.
        Admins and employee members will have access to billed activities that
        belong to the care team.

    delete:
        Deletes a :model:`billings.BilledActivity` instance.
        Only admins and employee owners are allowed to perform this action.
    """
    serializer_class = BilledActivitySerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsAdminOrEmployeeActivityOwner,
    )
    pagination_class = BilledActivityPagination
    queryset = BilledActivity.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = {
        'activity_datetime': ['lte'],
        'plan': ['exact'],
        'team_task_template': ['exact']
    }

    def get_queryset(self):
        qs = super(BilledActivityViewSet, self).get_queryset()
        user = self.request.user

        if user.is_superuser:
            pass

        if user.is_employee:
            employee = user.employee_profile
            if employee.organizations_managed.exists():
                organizations = employee.organizations_managed.all()
                qs = qs.filter(
                    plan__patient__facility__organization__in=organizations)
            elif employee.facilities_managed.exists():
                facilities = employee.facilities_managed.all()
                assigned_roles = employee.assigned_roles.all()
                qs = qs.filter(
                    Q(plan__patient__facility__in=facilities) |
                    Q(plan__care_team_members__in=assigned_roles)
                )
            else:
                assigned_roles = employee.assigned_roles.all()
                qs = qs.filter(plan__care_team_members__in=assigned_roles)

        elif user.is_patient:
            qs = qs.filter(
                plan__patient=user.patient_profile
            )

        return qs.distinct()

    @action(methods=['post'], detail=False,
            permission_classes=(permissions.IsAuthenticated, ))
    def track_time(self, request, *args, **kwargs):
        serializer = BilledActivitySerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        pre_activity = BilledActivity.objects.filter(plan_id=serializer.validated_data.get('plan'),
                                                     added_by_id=serializer.validated_data.get('added_by'),
                                                     activity_date=datetime.date.today()) \
                                             .first()
        if pre_activity:
            pre_activity.time_spent = pre_activity.time_spent + serializer.validated_data.get('time_spent')
            pre_activity.save()
        else:
            serializer.save()

        return Response(
            {"detail": _("Successfully created a billed activity for the plan.")}
        )

    @action(methods=['get'], detail=False,
            permission_classes=(permissions.IsAuthenticated, ))
    def total_tracked_time(self, request, *args, **kwargs):
        user = request.user
        spent_time = user.employee_profile.billable_hours if user.is_employee else 0

        return Response(
            {"total_tracked_time": spent_time}
        )


class OrganizationBilledActivity(ParentViewSetPermissionMixin,
                                 NestedViewSetMixin,
                                 mixins.ListModelMixin,
                                 viewsets.GenericViewSet):
    """

    list:
        Returns list of all :model:`billings.BilledActivity` objects related
        to the parent organization.
        Admins and employee members will have access to billed activities that
        belong to the care team.


    Filtering
    ---
    This endpoint also allows users to filter by `facility` and
    `service area`. Please see the examples below:

        - GET /api/organizations/<organization-ID>/billed_activities/?plan__patient__facility=<facility-ID>
        - GET /api/organizations/<organization-ID>/billed_activities/?plan_template__service_area=<service-area-ID>
        - GET /api/organizations/<organization-ID>/billed_activities/?plan__patient__facility=<facility-ID>&plan_template__service_area=<service-area-ID>


    """

    serializer_class = BilledActivitySerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsAdminOrEmployeeActivityOwner,
    )
    queryset = BilledActivity.objects.filter(
        plan__patient__payer_reimbursement=True)
    parent_lookup = [
        (
            'plan__patient__facility__organization',
            Organization,
            OrganizationViewSet
        )
    ]
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = {
        'plan__patient__facility': ['exact'],
        'plan__plan_template__service_area': ['exact'],
        'activity_datetime': ['lte'],
    }

    def get_queryset(self):
        queryset = super(OrganizationBilledActivity, self).get_queryset()
        user = self.request.user

        if user.is_superuser:
            pass

        elif user.is_employee:
            employee = user.employee_profile
            if employee.organizations_managed.exists():
                organizations = employee.organizations_managed.all()
                queryset = queryset.filter(
                    plan__patient__facility__organization__in=organizations)
            elif employee.facilities_managed.exists():
                facilities = employee.facilities_managed.all()
                assigned_roles = employee.assigned_roles.all()
                queryset = queryset.filter(
                    Q(plan__patient__facility__in=facilities) |
                    Q(plan__care_team_members__in=assigned_roles)
                )
            else:
                assigned_roles = employee.assigned_roles.all()
                queryset = queryset.filter(
                    plan__care_team_members__in=assigned_roles)

        elif user.is_patient:
            queryset = queryset.filter(
                plan__patient=user.patient_profile
            )

        return queryset.distinct()

    def _get_billable_patients(self, queryset):
        parents_query_dict = self.get_parents_query_dict()
        organization_id = parents_query_dict['plan__patient__facility__organization']

        patient_ids = queryset.filter(
            plan__patient__facility__organization__id=organization_id)\
            .values_list('plan__patient', flat=True).distinct()
        return PatientProfile.objects.filter(id__in=patient_ids)

    def get_billable_patients_count(self, queryset):
        patients = self._get_billable_patients(queryset)
        return patients.count()

    def get_total_facilities(self, queryset):
        patients = self._get_billable_patients(queryset)
        return patients.values_list('facility', flat=True).distinct().count()

    def get_total_practitioners(self, queryset):
        return queryset.values_list('plan__billing_practitioner',
                                    flat=True).distinct().count()

    @action(methods=['get'], detail=False)
    def overview(self, request, *args, **kwargs):
        """
        This endpoint will return aggregated data for an organization's billings.
        Aggregated data are as follows:

            - billable patients
            - total facilities
            - total practitioners
            - total hours
            - total billable

        Filtering
        ---
        This endpoint also allows users to filter by `facility` and
        `service area`. Please see the examples below:

            - GET /api/organizations/<organization-ID>/billed_activities/overview/?plan__patient__facility=<facility-ID>
            - GET /api/organizations/<organization-ID>/billed_activities/overview/?plan_template__service_area=<service-area-ID>
            - GET /api/organizations/<organization-ID>/billed_activities/overview/?plan__patient__facility=<facility-ID>&plan_template__service_area=<service-area-ID>
            - GET /api/organizations/<organization-ID>/billed_activities/overview/?activity_datetime__lte=2019

        Page Usage
        ---
        - this endpoint will be used in `billing` page

        """
        base_queryset = self.get_queryset()
        queryset = self.filter_queryset(base_queryset)

        # By default, filter queryset by current month and year if
        # query parameters for `activity_datetime` is not given
        query_parameters = self.request.query_params.keys()
        if 'activity_datetime__lte' not in query_parameters:
            now = timezone.now()
            queryset = queryset.filter(activity_datetime__lte=now)

        # TODO: Add this when details are provided
        total_billable = 0

        time_spent = queryset.aggregate(total=Sum('time_spent'))
        total_time_spent = time_spent['total'] or 0
        total_hours = str(datetime.timedelta(minutes=total_time_spent))[:-3]

        data = {
            'billable_patients': self.get_billable_patients_count(queryset),
            'total_facilities': self.get_total_facilities(queryset),
            'total_practitioners': self.get_total_practitioners(queryset),
            'total_hours': total_hours,
            'total_billable': total_billable
        }
        return Response(data=data)


class BillingTypeViewSet(viewsets.ModelViewSet):
    """
    Viewset for :model:`billings.BillingType`
    ========

    create:
        Creates :model:`billings.BillingType` object.
        Only admins and employees are allowed to perform this action.

    update:
        Updates :model:`billings.BillingType` object.
        Only admins and employees are allowed to perform this action.

    partial_update:
        Updates one or more fields of an existing plan template type object.
        Only admins and employees are allowed to perform this action.

    retrieve:
        Retrieves a :model:`billings.BillingType` instance.
        All users will have access to all template type objects.

    list:
        Returns list of all :model:`billings.BillingType` objects.
        All users will have access to all template type objects.

    delete:
        Deletes a :model:`billings.BillingType` instance.
        Only admins and employees are allowed to perform this action.
    """
    serializer_class = BillingTypeSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsEmployeeOrPatientReadOnly,
    )
    queryset = BillingType.objects.all()
