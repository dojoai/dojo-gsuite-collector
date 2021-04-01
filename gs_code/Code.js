function onOpen() {
    const ui = SpreadsheetApp.getUi();
    ui.createMenu('Dojo Collector')
        .addItem('Initialize Project (Create BigQuery Table)', 'createBQTable')
        .addSeparator()
        .addSubMenu(ui.createMenu('Initialize Collector')
            .addItem('Setup & Add Data to BigQuery', 'backendSettings')
            .addItem('Retrieve Data from BigQuery', 'frontendSettings'))
        .addSubMenu(ui.createMenu('Clear Data')
            .addItem('Clear Data From Spreadsheet', 'clearData')
            .addItem('Clear Data From BigQuery', 'clearDataBigQuery'))
        .addSubMenu(ui.createMenu('Utilities')
            .addItem('Open BigQuery', 'openBigQuery')
            .addItem('Open Cloud Run Services', 'openCloudRunServices')
            .addItem('Check Backend Status', 'backendStatus'))
        .addToUi();
}

function openBigQuery() {
    var ui = SpreadsheetApp.getUi();
    var configData = getConfigData()
    if (!configData.projectId || !configData.service_url || !configData.domains) {
        ui.alert('Missing Config Data. Please fill in the Project ID, Service URL and Domains in the Config Sheet.')
    } else {
        openUrl('https://console.cloud.google.com/bigquery?project=' + configData.projectId)
    }
}

function openCloudRunServices() {
    var ui = SpreadsheetApp.getUi();
    var configData = getConfigData()
    if (!configData.projectId || !configData.service_url || !configData.domains) {
        ui.alert('Missing Config Data. Please fill in the Project ID, Service URL and Domains in the Config Sheet.')
    } else {
        openUrl('https://console.cloud.google.com/run?project=' + configData.projectId)
    }
}

function getConfigData() {
    var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    var projectId = spreadsheet.getSheetByName('Config').getRange(1, 2).getValue()
    var service_url = spreadsheet.getSheetByName('Config').getRange(2, 2).getValue()
    var domains = spreadsheet.getSheetByName('Config').getRange(3, 2).getValue()


    return {projectId: projectId, service_url: service_url, domains: domains};
}

function openUrl(url) {
    var html = HtmlService.createHtmlOutput('<html lang=""><script>'
        + 'window.close = function(){window.setTimeout(function(){google.script.host.close()},9)};'
        + 'var a = document.createElement("a"); a.href="' + url + '"; a.target="_blank";'
        + 'if(document.createEvent){'
        + '  var event=document.createEvent("MouseEvents");'
        + '  if(navigator.userAgent.toLowerCase().indexOf("firefox")>-1){window.document.body.append(a)}'
        + '  event.initEvent("click",true,true); a.dispatchEvent(event);'
        + '}else{ a.click() }'
        + 'close();'
        + '</script>'

        + '<body style="word-break:break-word;font-family:sans-serif;">Failed to open automatically. <a href="' + url + '" target="_blank" onclick="window.close()">Click here to proceed</a>.</body>'
        + '<script>google.script.host.setHeight(40);google.script.host.setWidth(410)</script>'
        + '</html>')
        .setWidth(90).setHeight(1);
    SpreadsheetApp.getUi().showModalDialog(html, "Opening ...");
}

function backendStatus() {
    var ui = SpreadsheetApp.getUi();

    var configData = getConfigData()
    if (!configData.projectId || !configData.service_url || !configData.domains) {
        ui.alert('Missing Config Data. Please fill in the Project ID, Service URL and Domains in the Config Sheet.')
    } else {
        var bq_url = configData.service_url + '/status';
        var response = UrlFetchApp.fetch(bq_url);
        console.log("response", response)
        if (response) {
            ui.alert(response);
        } else {
            ui.alert("Something is wrong with your Cloud Run Service.");
        }
    }
}

function clearDataBigQuery() {
    var ui = SpreadsheetApp.getUi();

    var configData = getConfigData()
    if (!configData.projectId || !configData.service_url || !configData.domains) {
        ui.alert('Missing Config Data. Please fill in the Project ID, Service URL and Domains in the Config Sheet.')
    } else {
        var bq_url = configData.service_url + '/delete_backend_data/' + configData.projectId;
        var response = UrlFetchApp.fetch(bq_url);
        ui.alert(response);
    }
}

function createBQTable() {
    var ui = SpreadsheetApp.getUi();

    var configData = getConfigData()
    if (!configData.projectId || !configData.service_url || !configData.domains) {
        ui.alert('Missing Config Data. Please fill in the Project ID, Service URL and Domains in the Config Sheet.')
    } else {
        var bq_url = configData.service_url + '/create_bigquery_tables/' + configData.projectId;
        var response = UrlFetchApp.fetch(bq_url);
        ui.alert(response);
    }
}

function backendSettings() {
    var name = 'trigger_backend';
    var sidebar_title = 'Setup & Add Data to BigQuery';
    showSidebar(name, sidebar_title);
}

function frontendSettings() {
    var name = 'trigger_frontend';
    var sidebar_title = 'Retrieve Data from BigQuery';
    showSidebar(name, sidebar_title);
}

function showSidebar(html_name, sidebar_title) {
    var ui = SpreadsheetApp.getUi();
    var tmp = HtmlService.createTemplateFromFile(html_name);

    var html = tmp.evaluate();

    html.setTitle(sidebar_title);

    ui.showSidebar(html);
}

function getUserList() {
    var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = spreadsheet.getSheetByName('User List');
    var last_row = sheet.getLastRow();
    var last_columns = sheet.getLastColumn();
    var values = sheet.getRange(2, 1, last_row, last_columns).getValues();
    var list = '';
    for (var i = 0; i < values.length; i++) {
        if (values[i][0] !== '') {
            list = "'" + values[i][0] + "'," + list;
        }
    }
    list = list.replace(/^'',|,$/g, '');
    return list;
}

function runEmailQuery(start_date, end_date, projectId) {
    var email_sheet_name = 'Emails-List';
    var user_list = getUserList();
    var query_statement = "SELECT date, datetime, from_email, to_email, cc_email FROM `" + projectId + ".Dojo_Table.email_list` WHERE date BETWEEN DATE('" + start_date + "') AND DATE('" + end_date + "') and owner IN (" + user_list + ")";
    setHeader('email', email_sheet_name)
    runQuery(query_statement, email_sheet_name, projectId)
}

function runCalendarQuery(start_date, end_date, projectId) {
    var meet_sheet_name = 'Meetings-List';
    var user_list = getUserList();
    var query_statement = "SELECT date, datetime, num_Attendees, duration, location, attendees_list FROM `" + projectId + ".Dojo_Table.calendar_list` WHERE date BETWEEN DATE('" + start_date + "') AND DATE('" + end_date + "') and owner IN (" + user_list + ")";
    setHeader('calendar', meet_sheet_name);
    runQuery(query_statement, meet_sheet_name, projectId);
}

function runQuery(query_statement, sheet_name, projectId) {
    var request = {
        query: query_statement,
        useLegacySql: false
    };
    var queryResults = BigQuery.Jobs.query(request, projectId);
    var jobId = queryResults.jobReference.jobId;

    var sleepTimeMs = 500;
    while (!queryResults.jobComplete) {
        Utilities.sleep(sleepTimeMs);
        sleepTimeMs *= 2;
        queryResults = BigQuery.Jobs.getQueryResults(projectId, jobId);
    }

    var rows = queryResults.rows;
    while (queryResults.pageToken) {
        queryResults = BigQuery.Jobs.getQueryResults(projectId, jobId, {
            pageToken: queryResults.pageToken
        });
        rows = rows.concat(queryResults.rows);
    }
    output_raw_data(rows, sheet_name, queryResults)
}

function output_raw_data(rows, sheet_name, queryResults) {
    if (rows) {
        var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
        var sheet = spreadsheet.getSheetByName(sheet_name);

        var headers = queryResults.schema.fields.map(function (field) {
            return field.name;
        });
        sheet.appendRow(headers);

        var data = new Array(rows.length);
        for (var i = 0; i < rows.length; i++) {
            var cols = rows[i].f;
            data[i] = new Array(cols.length);
            for (var j = 0; j < cols.length; j++) {
                data[i][j] = cols[j].v;
            }
        }
        sheet.getRange(2, 1, rows.length, headers.length).setValues(data);
    } else {
        Logger.log('No rows returned.');
    }
}

function processBackendSettings(form) {
    var ui = SpreadsheetApp.getUi();
    var configData = getConfigData()
    if (!configData.projectId || !configData.service_url || !configData.domains) {
        ui.alert('Missing Config Data. Please fill in the Project ID, Service URL and Domains in the Config Sheet.')
    } else {
        var email_address = Session.getActiveUser().getEmail();

        var service_url = configData.service_url;
        var start = form.after;
        var end = form.before;
        var intext = form.intext;
        var appendOverwrite = form.appendOverwrite;
        var domain = configData.domains;
        var calendar = form.calendar;
        var email = form.email;
        var project_id = configData.projectId
        if (intext === undefined) {
            intext = 'int';
        }
        if (appendOverwrite === undefined) {
            appendOverwrite = 'overwrite';
        }
        var id = getSpreadsheetDetail()[0];
        var range = getSpreadsheetDetail()[1];
        if (calendar !== 'on') {
            calendar = 'off'
        }
        if (email !== 'on') {
            email = 'off'
        }
        var url = service_url + '/get_data?spreadsheetId=' + id + '&range=' + range + '&start=' + start + '&end=' + end +
            '&intext=' + intext + '&appendOverwrite=' + appendOverwrite + '&domain=' + domain + '&calendar=' + calendar + '&email=' + email + '&email_address=' + email_address + '&project_id=' + project_id;

        var response = UrlFetchApp.fetch(url);
        ui.alert(response)
    }
}

function processFrontendSettings(form) {
    var ui = SpreadsheetApp.getUi();
    var configData = getConfigData()
    if (!configData.projectId || !configData.service_url || !configData.domains) {
        ui.alert('Missing Config Data. Please fill in the Project ID, Service URL and Domains in the Config Sheet.')
    } else {
        var start = form.after;
        var end = form.before;
        var calendar = form.calendar;
        var email = form.email;
        if (calendar === 'on') {
            runCalendarQuery(start, end, configData.projectId);
        }
        if (email === 'on') {
            runEmailQuery(start, end, configData.projectId);
        }
    }
    ui.alert('Data copied from BigQuery to Emails-List / Meetings-List tabs. Please switch to one of those tabs.')
}

function getSpreadsheetDetail() {
    var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    var id = spreadsheet.getId();
    var range = spreadsheet.getSheetByName('User List').getDataRange().getA1Notation();
    var rangeString = 'User List!' + range;
    return [id, rangeString];
}

function setHeader(type, sheet_name) {
    var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = spreadsheet.getSheetByName(sheet_name);
    let header;
    if (type === 'email') {
        header = ['Date', 'Datetime', 'From', 'To', 'Cc'];
        sheet.getRange(1, 1, 1, 5).setValues([header]);
    }
    if (type === 'calendar') {
        header = ['Date', 'Datetime', 'Number of Attendees', 'Duration', 'Location', 'Attendees List'];
        sheet.getRange(1, 1, 1, 6).setValues([header]);
    }
}

function clearData() {
    var ui = SpreadsheetApp.getUi();
    var sheet_name = ['Emails-List', 'Meetings-List'];
    var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    for (let i = 0; i < sheet_name.length; i++) {
        const sheet = spreadsheet.getSheetByName(sheet_name[i]);
        const last_row = sheet.getLastRow();
        const last_columns = sheet.getLastColumn();
        sheet.getRange(2, 1, last_row, last_columns).clearContent();
    }
    ui.alert('The Emails-List and Meetings-List sheets have been cleared.')
}
