import { Component, OnInit } from '@angular/core';
import { ModalService } from '../../../modules/modals';
import { FormGroup, FormControl } from '@angular/forms';
import { ERROR_COLLECTOR_TOKEN } from '@angular/platform-browser-dynamic/src/compiler_factory';
import { omit as _omit } from 'lodash';
import { StoreService } from '../../../services';

@Component({
  selector: 'app-edit-task',
  templateUrl: './edit-task.component.html',
  styleUrls: ['./edit-task.component.scss'],
})
export class EditTaskComponent implements OnInit {

  public data = null;
  public totalPatients = 0;
  public frequencyOptions: Array<any> = [
    {displayName: 'Once', value: 'once'},
    {displayName: 'Daily', value: 'daily'},
    {displayName: 'Every Other Day', value: 'every_other_day'},
    {displayName: 'Weekly', value: 'weekly'},
    {displayName: 'Weekdays', value: 'weekdays'},
    {displayName: 'Weekends', value: 'weekends'},
  ];
  public task = null;
  public nameForm: FormGroup;
  public taskForm: FormGroup;
  public editName = false;
  public rolesChoices = [];
  public rolesSelected = [];
  public symptomChoices = [];
  public symptomsSelected = [];
  public categoriesChoices = ['notes', 'interaction', 'coordination'];

  public typeChoices = [
    {
      type: 'manager',
      title: 'Edit CM Task',
      dataModel: this.store.TeamTaskTemplate,
    },
    {
      type: 'team',
      title: 'Edit CT Task',
      dataModel: this.store.TeamTaskTemplate,
    },
    {
      type: 'patient',
      title: 'Edit Patient Task',
      dataModel: this.store.PatientTaskTemplate,
    },
    {
      type: 'assessment',
      title: 'Edit Assessment',
      dataModel: this.store.AssessmentTaskTemplate,
    },
    {
      type: 'symptom',
      title: 'Edit Symptom',
      dataModel: this.store.SymptomTaskTemplate,
    },
    {
      type: 'vital',
      title: 'Edit Vital',
      dataModel: this.store.VitalsTaskTemplate,
    },
    {
      type: 'medication',
      title: 'Edit Medication Task',
      dataModel: this.store.MedicationTaskTemplate,
    },
  ];
  public appearTimeHelpOpen = false;
  public dueTimeHelpOpen = false;
  public categoryHelpOpen = false;
  public symptomsDropOpen = false;
  public roleHelpOpen = false;
  public roleDropOpen = false;

  constructor(
    private modal: ModalService,
    private store: StoreService
  ) { }

  public ngOnInit() {
    if (this.data) {
      this.totalPatients = this.data.totalPatients ? this.data.totalPatients : 0;
      this.task = this.data && this.data.task ? this.data.task : {};
      this.initForm(this.task);
    }
  }

  public getTaskType() {
    if (!this.data || !this.data.type) {
      return this.typeChoices[0];
    } else {
      return this.typeChoices.find((obj) => obj.type === this.data.type);
    }
  }

  public updateTaskName() {
    if (!this.task) {
      return;
    }
    let keys = Object.keys(this.task);
    keys.forEach((key) => {
     if (this.nameForm.value[key] != undefined) {
        this.task[key] = this.nameForm.value[key];
      }
    });
    let updateSub = this.getTaskType().dataModel.update(this.task.id, {
      name: this.task.name,
    }, true).subscribe(
      (task) => {
        this.editName = false;
      },
      (err) => {},
      () => {
        updateSub.unsubscribe();
      }
    );
  }

  public initForm(task) {
    this.nameForm = new FormGroup({
      name: new FormControl(task.name),
    });
    this.taskForm = new FormGroup({
      start_on_day: new FormControl(task.start_on_day),
      frequency: new FormControl(task.frequency),
      repeat_amount_input: new FormControl(task.repeat_amount >=0 ? task.repeat_amount : 0),
      repeat_amount: new FormControl(task.repeat_amount),
      appear_time: new FormControl(task.appear_time),
      due_time: new FormControl(task.due_time),
    });
    if (this.getTaskType().type === 'symptom') {
      let defaultSymptomIds = task.default_symptoms.map((obj) => obj.id);
      this.taskForm.addControl('default_symptoms', new FormControl(defaultSymptomIds));
      this.fetchSymptoms().then((symptoms: any) => {
        this.symptomChoices = symptoms;
        this.symptomsSelected = task.default_symptoms;
      });
    }
    if (this.getTaskType().type === 'manager' || this.getTaskType().type === 'team') {
      this.taskForm.addControl('category', new FormControl(task.category));
    }
    if (this.getTaskType().type === 'team') {
      let roleIds = task.roles.map((obj) => obj.id)
      this.taskForm.addControl('roles', new FormControl(roleIds));
      this.fetchRoles().then((roles: any) => {
        this.rolesChoices = roles;
        this.rolesSelected = task.roles;
      });
    }
  }

  public updateFormFields() {
    let keys = Object.keys(this.task);
    keys.forEach((key) => {
     if (this.taskForm.value[key] != undefined) {
        if (key === 'repeat_amount' && this.taskForm.value['repeat_amount'] != -1){
          this.task[key] = this.taskForm.value['repeat_amount_input'];
        } else {
          this.task[key] = this.taskForm.value[key];
        }
      }
    });
  }

  public fetchSymptoms() {
    let promise = new Promise((resolve, reject) => {
      let symptomsSub = this.store.Symptom.readListPaged().subscribe(
        (symptoms) => resolve(symptoms),
        (err) => reject(err),
        () => {
          symptomsSub.unsubscribe();
        },
      );
    });
    return promise;
  }

  public fetchRoles() {
    let promise = new Promise((resolve, reject) => {
      let rolesSub = this.store.ProviderRole.readListPaged().subscribe(
        (roles) => resolve(roles),
        (err) => reject(err),
        () => {
          rolesSub.unsubscribe();
        },
      );
    });
    return promise;
  }

  public isSymptomSelected(symptom) {
    return this.symptomsSelected.findIndex((obj) => obj.id === symptom.id) > -1;
  }

  public toggleSymptomSelected(symptom) {
    let index = this.symptomsSelected.findIndex((obj) => obj.id === symptom.id);
    if (index > -1) {
      this.symptomsSelected.splice(index, 1);
    } else {
      this.symptomsSelected.push(symptom);
    }
    let selectedIds = this.symptomsSelected.map((obj) => obj.id);
    this.taskForm.controls['default_symptoms'].setValue(selectedIds);
  }

  public formatSelectedSymptoms() {
    if (!this.symptomsSelected || this.symptomsSelected.length < 1) {
      return '';
    }
    if (this.symptomsSelected.length > 1) {
      return `${this.symptomsSelected[0].name}, +${this.symptomsSelected.length - 1}`
    } else {
      return this.symptomsSelected[0].name;
    }
  }

  public isRoleSelected(role) {
    return this.rolesSelected.findIndex((obj) => obj.id === role.id) > -1;
  }

  public toggleRoleSelected(role) {
    let index = this.rolesSelected.findIndex((obj) => obj.id === role.id);
    if (index > -1) {
      this.rolesSelected.splice(index, 1);
    } else {
      this.rolesSelected.push(role);
    }
    let selectedIds = this.rolesSelected.map((obj) => obj.id);
    this.taskForm.controls['roles'].setValue(selectedIds);
  }

  public formatSelectedRoles() {
    if (!this.rolesSelected || this.rolesSelected.length < 1) {
      return '';
    }
    if (this.rolesSelected.length > 1) {
      return `${this.rolesSelected[0].name}, +${this.rolesSelected.length - 1}`
    } else {
      return this.rolesSelected[0].name;
    }
  }

  public createTask() {
    let createSub = this.getTaskType().dataModel.create(this.task).subscribe(
      (task) => {
        this.modal.close(task);
      },
      (err) => {},
      () => {
        createSub.unsubscribe();
      },
    );
  }

  public updateTask() {
    let postData = Object.assign({}, this.task);
    if (this.getTaskType().type === 'medication') {
      postData = _omit(postData, 'patient_medication');
    }
    postData = _omit(postData, 'id');
    let updateSub = this.getTaskType().dataModel.update(this.task.id, postData, true).subscribe(
      (task) => {
        this.modal.close(task);
      },
      (err) => {},
      () => {
        updateSub.unsubscribe();
      },
    );
  }

  public submitTask() {
    this.updateFormFields();
    if (this.getTaskType().type === 'manager') {
      this.task.is_manager_task = true;
    }
    this.updateTask();
  }

  public close() {
    this.modal.close(null);
  }

  public saveDisabled() {
    if (this.getTaskType().type === 'symptom') {
      return this.symptomsSelected.length < 1;
    }
  }
}
