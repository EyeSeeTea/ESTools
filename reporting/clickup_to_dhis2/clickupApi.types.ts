import axios from 'axios';

export interface Team {
    id: string;
    name: string;
}
  
export interface TimeEntry {
  task: {
    id: string;
    name: string;
  };
  duration: number;
  billable: boolean;
  task_location: {
    list_id: string;
  };
}

export interface List {
  id: string;
  name: string;
}

export interface CustomField {
  id: string;
  name: string;
  custom_item_id: number;
}

export interface TaskDetails {
  custom_fields: CustomField[];
  time_estimate: string;
  custom_item_id: number;
}