import axios from 'axios';
import * as fs from 'fs';

import { Team, TimeEntry, List, CustomField, TaskDetails } from "./clickupApi.types";
import { getUnixTimeForLastNDays, formatDuration } from "./utils/unixtime";

// Load configuration from config.json
const config = JSON.parse(fs.readFileSync('config.json', 'utf-8'));

export const apiToken: string = config.apiToken;
export const lastNDays: number = config.lastNDays;

const baseUrl = "https://api.clickup.com/api/v2";

export class ClickupApi {
  private apiToken: string;

  constructor(apiToken: string) {
    this.apiToken = apiToken;
  }

  async getTeams(): Promise<Team[]> {
    const url = `${baseUrl}/team`;

    try {
      const response = await axios.get(url, {
        headers: { 'Authorization': this.apiToken }
      });

      const teams: Team[] = response.data.teams;
      return teams;
    } catch (error) {
      console.error('Error fetching teams:', error);
      return [];
    }
  }

  async getTimeEntriesForTeam(teamId: string, startDate: number, endDate: number): Promise<TimeEntry[]> {
    const url = `${baseUrl}/team/${teamId}/time_entries/?start_date=${startDate}&end_date=${endDate}`;

    try {
      const response = await axios.get(url, {
        headers: { 'Authorization': this.apiToken }
      });

      const timeEntries: TimeEntry[] = response.data.data;
      return timeEntries.filter(entry => entry.duration !== 0); // Filter out entries with no duration
    } catch (error) {
      console.error(`Error fetching time entries for team ${teamId}:`, error);
      return [];
    }
  }

  async getListName(listId: string): Promise<string> {
    const url = `${baseUrl}/list/${listId}`;

    try {
      const response = await axios.get(url, {
        headers: { 'Authorization': this.apiToken }
      });

      const list: List = response.data;
      return list.name;
    } catch (error) {
      console.error(`Error fetching list name for list ID ${listId}:`, error);
      return 'Unknown List';
    }
  }

  async getTaskDetails(taskId: string): Promise<{ customFields: CustomField[], timeEstimate: string, customItemId: number }> {
    const url = `${baseUrl}/task/${taskId}`;

    try {
      const response = await axios.get(url, {
        headers: { 'Authorization': this.apiToken }
      });

      const taskDetails: TaskDetails = response.data;
      return {
        customFields: taskDetails.custom_fields,
        timeEstimate: taskDetails.time_estimate,
        customItemId: taskDetails.custom_item_id
      };
    } catch (error) {
      console.error(`Error fetching task details for task ID ${taskId}:`, error);
      return {
        customFields: [],
        timeEstimate: 'N/A',
        customItemId: 0
      };
    }
  }
}