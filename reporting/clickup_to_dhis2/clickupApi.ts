import axios from 'axios';
import fs from 'fs';

const config = JSON.parse(fs.readFileSync('config.json', 'utf-8'));

const apiToken: string = config.apiToken;
const lastNDays: number = config.lastNDays;

interface Team {
  id: string;
  name: string;
}

interface TimeEntry {
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

interface List {
  id: string;
  name: string;
}

interface CustomField {
  id: string;
  name: string;
}

interface TaskDetails {
  custom_fields: CustomField[];
  time_estimate: string;
}

async function getTeams(apiToken: string): Promise<Team[]> {
  const url = `https://api.clickup.com/api/v2/team`;

  try {
    const response = await axios.get(url, {
      headers: {
        'Authorization': apiToken
      }
    });

    const teams: Team[] = response.data.teams;

    return teams;
  } catch (error) {
    console.error('Error fetching teams:', error);
    return [];
  }
}

async function getTimeEntriesForTeam(teamId: string, startDate: number, endDate: number, apiToken: string): Promise<TimeEntry[]> {
  const url = `https://api.clickup.com/api/v2/team/${teamId}/time_entries/?start_date=${startDate}&end_date=${endDate}`;

  try {
    const response = await axios.get(url, {
      headers: {
        'Authorization': apiToken
      }
    });

    const timeEntries: TimeEntry[] = response.data.data;
    
    const filteredTasks = timeEntries.filter(entry => entry.duration !== 0);

    return filteredTasks;
  } catch (error) {
    console.error(`Error fetching time entries for team ${teamId}:`, error);
    return [];
  }
}

async function getListName(listId: string, apiToken: string): Promise<string> {
  const url = `https://api.clickup.com/api/v2/list/${listId}`;

  try {
    const response = await axios.get(url, {
      headers: {
        'Authorization': apiToken
      }
    });

    const list: List = response.data;
    return list.name;
  } catch (error) {
    console.error(`Error fetching list name for list ID ${listId}:`, error);
    return 'Unknown List';
  }
}

async function getTaskDetails(taskId: string, apiToken: string): Promise<{ customFields: CustomField[], timeEstimate: string }> {
  const url = `https://api.clickup.com/api/v2/task/${taskId}`;

  try {
    const response = await axios.get(url, {
      headers: {
        'Authorization': apiToken
      }
    });

    const taskDetails: TaskDetails = response.data;
    return {
      customFields: taskDetails.custom_fields,
      timeEstimate: taskDetails.time_estimate
    };
  } catch (error) {
    console.error(`Error fetching task details for task ID ${taskId}:`, error);
    return {
      customFields: [],
      timeEstimate: 'N/A'
    };
  }
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  return `${hours}h ${minutes}m ${seconds}s`;
}

function getUnixTimeForLastNDays(n: number): { startUnixTime: number, endUnixTime: number } {
  const now = new Date();
  const endUnixTime = now.getTime(); // Current time in milliseconds

  const startDate = new Date(now);
  startDate.setDate(now.getDate() - n);
  const startUnixTime = startDate.getTime(); // n days before now in milliseconds

  return { startUnixTime, endUnixTime };
}

async function getAllTeamsTimeEntries(apiToken: string, lastNDays: number): Promise<void> {
  const teams = await getTeams(apiToken);

  // Calculate start and end dates in Unix time
  const { startUnixTime, endUnixTime } = getUnixTimeForLastNDays(lastNDays);

  for (const team of teams) {
    console.log(`Fetching time entries for team: ${team.name} (ID: ${team.id})`);

    const tasks = await getTimeEntriesForTeam(team.id, startUnixTime, endUnixTime, apiToken);

    if (tasks.length > 0) {
      // Aggregate durations by task ID
      const taskDurations: { 
        [taskId: string]: { 
          name: string; 
          totalDuration: number; 
          listId: string; 
          customFields: CustomField[];
          timeEstimate: string; 
          billable: boolean;
        } 
      } = {};

      for (const task of tasks) {
        const taskId = task.task.id;
        const duration = Number(task.duration); // Ensure the duration is treated as a number
        
        if (!taskDurations[taskId]) {
          const { customFields, timeEstimate } = await getTaskDetails(taskId, apiToken);

          taskDurations[taskId] = {
            name: task.task.name,
            totalDuration: 0,
            listId: task.task_location.list_id,
            customFields,
            timeEstimate,
            billable: task.billable
          };
        }

        taskDurations[taskId].totalDuration += duration;
      }

      console.log(`Tasks with time tracked for team ${team.name}:`);
      for (const taskId of Object.keys(taskDurations)) {
        const formattedDuration = formatDuration(taskDurations[taskId].totalDuration);
        const listName = await getListName(taskDurations[taskId].listId, apiToken);
        console.log(`Task ID: ${taskId}, Task Name: ${taskDurations[taskId].name}, List Name: ${listName}, Time Estimate: ${taskDurations[taskId].timeEstimate}, Billable: ${taskDurations[taskId].billable}, Total Duration: ${formattedDuration}`);

        // Print custom fields
        taskDurations[taskId].customFields.forEach(field => {
          console.log(`   Custom Field ID: ${field.id}, Name: ${field.name}`);
        });
      }
    } else {
      console.log(`No tasks with time tracked for team ${team.name}.`);
    }
  }
}

getAllTeamsTimeEntries(apiToken, lastNDays)
  .then(() => {
    console.log('Finished fetching time entries for all teams.');
  })
  .catch(error => {
    console.error('Error:', error);
  });
