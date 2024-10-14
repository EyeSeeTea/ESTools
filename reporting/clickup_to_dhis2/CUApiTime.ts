import { ClickupApi, apiToken, lastNDays } from "./CUApi";
import { getUnixTimeForLastNDays, formatDuration } from "./utils/unixtime";

class TeamTimeTracker {
    private clickupApi: ClickupApi;
  
    constructor(clickupApi: ClickupApi) {
      this.clickupApi = clickupApi;
    }
  
    async trackTimeForTeams(lastNDays: number) {
      const teams = await this.clickupApi.getTeams();
  
      // Calculate start and end dates in Unix time
      const { startUnixTime, endUnixTime } = getUnixTimeForLastNDays(lastNDays);

      const output: any[] = [];
  
      for (const team of teams) {
        console.log(`Fetching time entries for team: ${team.name} (ID: ${team.id})`);
  
        const tasks = await this.clickupApi.getTimeEntriesForTeam(team.id, startUnixTime, endUnixTime);

        if (tasks.length > 0) {
            const teamDetails: any = {
              teamId: team.id,
              teamName: team.name,
              lists: []
            };

            const listDurations: { 
              [listId: string]: { 
                [customItemId: string]: { 
                  listName: string;
                  trackedTime: { billableDuration: number; nonBillableDuration: number }; 
                  estimatedTime: { billableDuration: number; nonBillableDuration: number } 
                } 
              } 
            } = {};

            for (const task of tasks) {
                const taskId = task.task.id;
                const duration = Number(task.duration);
                const taskDetails = await this.clickupApi.getTaskDetails(taskId);
                const customItemId = taskDetails.customItemId;
                const timeEstimate = taskDetails.timeEstimate ? Number(taskDetails.timeEstimate) : 0;

                const listId = task.task_location.list_id;
                const customItemIdStr = String(customItemId); // Convert customItemId to string

                if (!listDurations[listId]) {
                  const listName = await this.clickupApi.getListName(listId);
                  listDurations[listId] = {};
                }
              
                if (!listDurations[listId][customItemIdStr]) {
                  listDurations[listId][customItemIdStr] = {
                    listName: await this.clickupApi.getListName(listId),
                    trackedTime: {
                      billableDuration: 0,
                      nonBillableDuration: 0
                    },
                    estimatedTime: {
                      billableDuration: 0,
                      nonBillableDuration: 0
                    }
                  };
                }
      
                // Add tracked time to either billable or non-billable total
                if (task.billable) {
                  listDurations[listId][customItemIdStr].trackedTime.billableDuration += duration;
                } else {
                  listDurations[listId][customItemIdStr].trackedTime.nonBillableDuration += duration;
                }

                // Add estimated time to either billable or non-billable total
                if (task.billable) {
                  listDurations[listId][customItemIdStr].estimatedTime.billableDuration += timeEstimate;
                } else {
                  listDurations[listId][customItemIdStr].estimatedTime.nonBillableDuration += timeEstimate;
                }
              }

              // Add list-level totals to the output
              for (const listId of Object.keys(listDurations)) {
                const listOutput: any = {
                  listId: listId,
                  listName: listDurations[listId][Object.keys(listDurations[listId])[0]].listName,
                  customItemGroups: []
                };
      
                for (const customItemIdStr of Object.keys(listDurations[listId])) {
                  const customItemGroup = {
                    customItemId: Number(customItemIdStr), // Convert back to number for output
                    trackedTime: {
                      billableDuration: formatDuration(listDurations[listId][customItemIdStr].trackedTime.billableDuration),
                      nonBillableDuration: formatDuration(listDurations[listId][customItemIdStr].trackedTime.nonBillableDuration)
                    },
                    estimatedTime: {
                      billableDuration: formatDuration(listDurations[listId][customItemIdStr].estimatedTime.billableDuration),
                      nonBillableDuration: formatDuration(listDurations[listId][customItemIdStr].estimatedTime.nonBillableDuration)
                    }
                  };
                  listOutput.customItemGroups.push(customItemGroup);
                }
      
                teamDetails.lists.push(listOutput);
              }
  
              // Add team details to the final output
              output.push(teamDetails);

        } else {
          console.log(`No tasks with time tracked for team ${team.name}.`);
        }
      }
      const jsonOutput = JSON.stringify(output, null, 2);
      console.log(jsonOutput); // Output in JSON format
    }
}
  
  // Example Usage
  const clickupApi = new ClickupApi(apiToken);
  const teamTimeTracker = new TeamTimeTracker(clickupApi);
  
  // Call the async method from the TeamTimeTracker class
  teamTimeTracker.trackTimeForTeams(lastNDays)
    .then(() => console.log('Time tracking complete'))
    .catch(error => console.error('Error tracking time:', error));
  