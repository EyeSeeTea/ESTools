import datetime
import requests
import argparse
import json


def chunk_list(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def download_data(server, auth, data_type, ids):
    all_data = []  
    base_url = f"https://{server}/api/{data_type}.json"

    ids = ids[0].split(',')
    print(ids)
    for id_chunk in chunk_list(ids, 50):
        url = f"{base_url}?filter=id:in:[{','.join(id_chunk)}]&paging=false&fields=*"
        print(url)
        response = requests.get(url, auth=auth)
        if response.status_code == 200:
            chunk_data = response.json()
            all_data.extend(chunk_data.get(data_type, []))
        else:
            print(f"Error fetching data for IDs {id_chunk}: {response.status_code}")
    return all_data

def main():
    parser = argparse.ArgumentParser(description="Download data from API.")
    parser.add_argument("--server", required=True, help="Server address")
    parser.add_argument("--user", required=True, help="User for authentication")
    parser.add_argument("--password", required=True, help="Password for authentication")
    parser.add_argument("--name", required=False, help="Name for the file")
    parser.add_argument("--data_type", choices=["programStageSections","programIndicatorGroups","dataElements","eventFilters","indicators","options","sections","programs","dataSets","validationRuleGroups","externalMapLayers","programStages","constants","eventCharts","externalFileResources","programIndicators","dataElementOperands","trackedEntityTypes","categoryOptionGroupSets","dataApprovalLevels","programTrackedEntityAttributeGroups","programNotificationTemplates","dataSetNotificationTemplates","dataApprovalWorkflows","validationResults","organisationUnitLevels","analyticsTableHooks","predictors","interpretations","programSections","reports","indicatorGroups","validationRules","messageConversations","programRuleVariables","trackedEntityAttributes","categories","icons","pushAnalysis","dataStores","apiToken","organisationUnits","sqlViews","categoryOptionCombos","userGroups","trackedEntityInstances","proposals","optionGroups","metadataVersions","organisationUnitGroupSets","documents","dashboards","programDataElements","legendSets","programRuleActions","predictorGroups","smsCommands","oAuth2Clients","users","indicatorTypes","eventVisualizations","indicatorGroupSets","eventReports","dataElementGroups","minMaxDataElements","categoryOptions","optionSets","fileResources","dashboardItems","categoryCombos","programRules","userRoles","dataElementGroupSets","trackedEntityInstanceFilters","categoryOptionGroups","attributes","optionGroupSets","visualizations","jobConfigurations","organisationUnitGroups","mapViews","maps","dataEntryForms","relationshipTypes","validationNotificationTemplates","relationships"], required=True, help="Type of data to download")
    parser.add_argument("--ids", nargs="+", help="List of IDs to download")
    parser.add_argument("--ids_file", help="File containing IDs to download")
    
    args = parser.parse_args()

    if not args.ids and not args.ids_file:
        print("You must provide either --ids or --ids_file.")
        return

    if args.ids_file:
        with open(args.ids_file, 'r') as file:
            ids = [line.strip() for line in file.readlines()]
    else:
        ids = args.ids

    auth = (args.user, args.password)
    data = download_data(args.server, auth, args.data_type, ids)

    if data:
        date = datetime.datetime.now().isoformat().split('T')[0]
        with open(f"{args.name}_{args.data_type}_{date}_data.json", 'w') as outfile:
            json.dump({args.data_type: data}, outfile, indent=4, ensure_ascii=False)
        print(f"Data downloaded to {args.name}_{args.data_type}_{date}_data.json")

if __name__ == "__main__":
    main()