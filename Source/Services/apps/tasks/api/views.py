from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import (
    PatientTaskTemplate,
    PatientTask,
    TeamTaskTemplate,
    TeamTask,
    MedicationTaskTemplate,
    MedicationTask,
    SymptomTaskTemplate,
    SymptomTask,
    SymptomRating,
    AssessmentTaskTemplate,
    AssessmentQuestion,
    AssessmentTask,
    AssessmentResponse,
    VitalTaskTemplate,
    VitalTask,
    VitalQuestion,
    VitalResponse,
)
from ..permissions import (
    IsPatientOrEmployeeForTask,
    IsPatientOrEmployeeReadOnly,
    IsEmployeeOrPatientReadOnly,
)
from ..utils import get_all_tasks_for_today
from .filters import DurationFilter
from . serializers import (
    PatientTaskTemplateSerializer,
    PatientTaskSerializer,
    TeamTaskTemplateSerializer,
    TeamTaskSerializer,
    MedicationTaskTemplateSerializer,
    MedicationTaskSerializer,
    SymptomTaskTemplateSerializer,
    SymptomTaskSerializer,
    SymptomRatingSerializer,
    AssessmentTaskTemplateSerializer,
    AssessmentQuestionSerializer,
    AssessmentTaskSerializer,
    AssessmentResponseSerializer,
    VitalTaskTemplateSerializer,
    VitalTaskSerializer,
    VitalQuestionSerializer,
    VitalResponseSerializer,
)
from care_adopt_backend import utils
from care_adopt_backend.permissions import (
    EmployeeOrReadOnly,
)


class PatientTaskTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = PatientTaskTemplateSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = PatientTaskTemplate.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'plan_template__id',
    )

    def get_queryset(self):
        queryset = super(PatientTaskTemplateViewSet, self).get_queryset()
        employee_profile = utils.employee_profile_or_none(self.request.user)
        patient_profile = utils.patient_profile_or_none(self.request.user)

        if employee_profile is not None:
            # TODO: Only get task templates for patients this employee
            # has access to
            return queryset
        elif patient_profile is not None:
            patient_plans = patient_profile.care_plans.all()
            plan_templates = patient_plans.values_list("plan_template",
                                                       flat=True)
            queryset = queryset.filter(plan_template__id__in=plan_templates)
            return queryset
        else:
            return queryset


class PatientTaskViewSet(viewsets.ModelViewSet):
    serializer_class = PatientTaskSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPatientOrEmployeeForTask,
    )
    queryset = PatientTask.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'plan__id',
        'patient_task_template__id',
        'plan__patient__id',
        'status',
    )

    def get_queryset(self):
        queryset = super(PatientTaskViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(plan__patient=user.patient_profile)

        return queryset


class TeamTaskTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = TeamTaskTemplateSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = TeamTaskTemplate.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'plan_template__id',
    )


class TeamTaskViewSet(viewsets.ModelViewSet):
    serializer_class = TeamTaskSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = TeamTask.objects.all()


class MedicationTaskTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = MedicationTaskTemplateSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsEmployeeOrPatientReadOnly,
    )
    queryset = MedicationTaskTemplate.objects.all()


class MedicationTaskViewSet(viewsets.ModelViewSet):
    serializer_class = MedicationTaskSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPatientOrEmployeeForTask,
    )
    queryset = MedicationTask.objects.all()
    filter_backends = (DjangoFilterBackend, DurationFilter)
    filterset_fields = (
        'medication_task_template__plan__id',
        'medication_task_template__id',
        'medication_task_template__plan__patient__id',
        'status',
    )

    def get_queryset(self):
        queryset = super(MedicationTaskViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                medication_task_template__plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(medication_task_template__plan__patient=user.patient_profile)

        return queryset


class SymptomTaskTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = SymptomTaskTemplateSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = SymptomTaskTemplate.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'plan_template__id',
    )


class SymptomTaskViewSet(viewsets.ModelViewSet):
    serializer_class = SymptomTaskSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPatientOrEmployeeForTask,
    )
    queryset = SymptomTask.objects.all()
    filter_backends = (DjangoFilterBackend, DurationFilter)
    filterset_fields = (
        'plan__id',
        'symptom_task_template__id',
        'plan__patient__id',
        'is_complete',
    )

    def get_queryset(self):
        queryset = super(SymptomTaskViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(plan__patient=user.patient_profile)

        return queryset


class SymptomRatingViewSet(viewsets.ModelViewSet):
    serializer_class = SymptomRatingSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPatientOrEmployeeReadOnly,
    )
    queryset = SymptomRating.objects.all()

    def get_queryset(self):
        queryset = super(SymptomRatingViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                symptom_task__plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(
                symptom_task__plan__patient=user.patient_profile
            )

        return queryset


class AssessmentTaskTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentTaskTemplateSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'plan_template__id',
    )
    queryset = AssessmentTaskTemplate.objects.all()


class AssessmentQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentQuestionSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = AssessmentQuestion.objects.all()


class AssessmentTaskViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentTaskSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPatientOrEmployeeForTask,
    )
    queryset = AssessmentTask.objects.all()
    filter_backends = (DjangoFilterBackend, DurationFilter)
    filterset_fields = (
        'plan__id',
        'assessment_task_template__id',
        'plan__patient__id',
    )

    def get_queryset(self):
        queryset = super(AssessmentTaskViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(plan__patient=user.patient_profile)

        return queryset


class AssessmentResponseViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentResponseSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPatientOrEmployeeReadOnly,
    )
    queryset = AssessmentResponse.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'assessment_task__id',
        'assessment_question__id',
    )

    def get_queryset(self):
        queryset = super(AssessmentResponseViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                assessment_task__plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(
                assessment_task__plan__patient=user.patient_profile
            )

        return queryset

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'POST' and isinstance(self.request.data, list):
            kwargs['many'] = True
        return super(AssessmentResponseViewSet, self).get_serializer(
            *args, **kwargs)


class VitalTaskTemplateViewSet(viewsets.ModelViewSet):
    """
    Viewset for :model:`tasks.VitalTaskTemplate`
    ========

    create:
        Creates :model:`tasks.VitalTaskTemplate` object.
        Only admins and employees are allowed to perform this action.

    update:
        Updates :model:`tasks.VitalTaskTemplate` object.
        Only admins and employees are allowed to perform this action.

    partial_update:
        Updates one or more fields of an existing vital task template object.
        Only admins and employees are allowed to perform this action.

    retrieve:
        Retrieves a :model:`tasks.VitalTaskTemplate` instance.

    list:
        Returns list of all :model:`tasks.VitalTaskTemplate` objects.

    delete:
        Deletes a :model:`tasks.VitalTaskTemplate` instance.
        Only admins and employees are allowed to perform this action.
    """
    serializer_class = VitalTaskTemplateSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsEmployeeOrPatientReadOnly,
    )
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'plan_template__id',
    )
    queryset = VitalTaskTemplate.objects.all()


class VitalTaskViewSet(viewsets.ModelViewSet):
    """
    Viewset for :model:`tasks.VitalTask`
    ========

    create:
        Creates :model:`tasks.VitalTask` object.
        Only admins and employees are allowed to perform this action.

    update:
        Updates :model:`tasks.VitalTask` object.
        Only admins and employees who belong to the same care team are allowed
        to perform this action.

    partial_update:
        Updates one or more fields of an existing vital task object.
        Only admins and employees who belong to the same care team are allowed
        to perform this action.

    retrieve:
        Retrieves a :model:`tasks.VitalTask` instance.
        Admins will have access to all vital tasks objects. Employees will only
        have access to those vital tasks belonging to its own care team.
        Patients will have access to all vital tasks assigned to them.

    list:
        Returns list of all :model:`tasks.VitalTask` objects.
        Admins will get all existing vital task objects. Employees will get the
        vital tasks belonging to a certain care team. Patients will get all
        vital tasks belonging to them.

    delete:
        Deletes a :model:`tasks.VitalTask` instance.
        Only admins and employees who belong to the same care team are allowed
        to perform this action.
    """
    serializer_class = VitalTaskSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsEmployeeOrPatientReadOnly,
    )
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'is_complete',
    )
    queryset = VitalTask.objects.all()

    def get_queryset(self):
        queryset = super(VitalTaskViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(plan__patient=user.patient_profile)

        return queryset


class VitalQuestionViewSet(viewsets.ModelViewSet):
    """
    Viewset for :model:`tasks.VitalQuestion`
    ========

    create:
        Creates :model:`tasks.VitalQuestion` object.
        Only admins and employees are allowed to perform this action.

    update:
        Updates :model:`tasks.VitalQuestion` object.
        Only admins and employees are allowed to perform this action.

    partial_update:
        Updates one or more fields of an existing vital question object.
        Only admins and employees are allowed to perform this action.

    retrieve:
        Retrieves a :model:`tasks.VitalQuestion` instance.

    list:
        Returns list of all :model:`tasks.VitalQuestion` objects.

    delete:
        Deletes a :model:`tasks.VitalQuestion` instance.
        Only admins and employees are allowed to perform this action.
    """
    serializer_class = VitalQuestionSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsEmployeeOrPatientReadOnly,
    )
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'vital_task_template',
    )
    queryset = VitalQuestion.objects.all()


class VitalResponseViewSet(viewsets.ModelViewSet):
    """
    Viewset for :model:`tasks.VitalResponse`
    ========

    create:
        Creates :model:`tasks.VitalResponse` object.
        Only admins and patients are allowed to perform this action.

    update:
        Updates :model:`tasks.VitalResponse` object.
        Only admins and patients who own the plan are allowed to perform this
        action.

    partial_update:
        Updates one or more fields of an existing vital task object.
        Only admins and patients who own the plan are allowed to perform this
        action.

    retrieve:
        Retrieves a :model:`tasks.VitalResponse` instance.
        Admins will have access to all vital responses objects. Employees will
        only have access to those vital responses belonging to its own care
        team. Patients will have access to all vital responses assigned to
        them.

    list:
        Returns list of all :model:`tasks.VitalResponse` objects.
        Admins will get all existing vital task objects. Employees will get the
        vital responses belonging to their care team. Patients will get all
        vital responses belonging to them.

    delete:
        Deletes a :model:`tasks.VitalResponse` instance.
        Only admins and patients who own the plan are allowed to perform this
        action.
    """
    serializer_class = VitalResponseSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPatientOrEmployeeReadOnly,
    )
    queryset = VitalResponse.objects.all()

    def get_queryset(self):
        queryset = super(VitalResponseViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                vital_task__plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(
                vital_task__plan__patient=user.patient_profile
            )

        return queryset

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'POST' and \
           isinstance(self.request.data, list):
            kwargs['many'] = True
        return super(VitalResponseViewSet, self).get_serializer(
            *args, **kwargs)


############################
# ----- CUSTOM VIEWS ----- #
############################

class TodaysTasksAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request, format=None):
        tasks = get_all_tasks_for_today(request.user)
        return Response(data=tasks)