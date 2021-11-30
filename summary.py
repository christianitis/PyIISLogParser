import datetime
import datetime as dt
import exchangelib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from exchangelib import attachments

# TODO: All of this needs a major cleanup, it looks like total crap
import wineventlog

total_requests = 0
total_errors = 0

requests_by_time = {}
errors_by_time = {}


def increment_rbt(datet: datetime.datetime, iserror: bool):
    # To round it to the hour for better display on the chart/smaller memory footprint (maybe?)
    hour_dt = dt.datetime.strptime(datet.strftime("%m/%d/%y %H:00:00"), "%m/%d/%y %H:%M:%S")

    if iserror:
        if not errors_by_time.__contains__(hour_dt):
            errors_by_time[hour_dt] = 1
        else:
            errors_by_time[hour_dt] += 1

    else:
        if not requests_by_time.__contains__(hour_dt):
            requests_by_time[hour_dt] = 1
        else:
            requests_by_time[hour_dt] += 1


def initialize(cursor, logdays):
    print("Done loading logs, creating charts...")
    cursor.execute("SELECT dt, status FROM logtable;")

    for row in cursor.fetchall():
        datet = dt.datetime.fromisoformat(row[0])
        if row[1] >= 500:
            # print("inc error")
            increment_rbt(datet, True)
        else:
            # print("inc normal")
            increment_rbt(datet, False)

    plt.title("Requests/Errors Per Day (Per Hour)")
    plt.gca().xaxis_date()
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.plot(requests_by_time.keys(), requests_by_time.values())
    plt.plot(errors_by_time.keys(), errors_by_time.values())
    plt.tick_params(labelsize=4)
    plt.gcf().autofmt_xdate()
    plt.savefig("requestsanderrors.png")
    plt.close()

    cursor.execute("SELECT uri, COUNT(*) AS c FROM logtable GROUP BY uri HAVING c > 1 ORDER BY c DESC LIMIT 10;")

    most_requested_pages = {}
    for row in cursor.fetchall():
        most_requested_pages[row[0]] = row[1]

    plt.pie(most_requested_pages.values(), labels=most_requested_pages.keys(), textprops={'fontsize': 6},
            rotatelabels=True, labeldistance=0.23)
    plt.title("10 Most Requested Pages")
    plt.savefig("mostviewedpages.png")
    plt.close()

    cursor.execute(
        "SELECT uri, COUNT(*) FROM logtable WHERE status >= 400 GROUP BY uri ORDER BY COUNT(*) DESC LIMIT 20;")
    errors_by_page = {}
    for row in cursor.fetchall():
        errors_by_page[row[0]] = int(row[1])

    y_pos = np.arange(len(errors_by_page.keys()))
    plt.barh(y_pos, errors_by_page.values(), color=(1, 0, 0, 1))
    plt.yticks(y_pos, errors_by_page.keys(), fontsize='x-small')
    plt.title("Top 20 Most Erroneous Pages")
    plt.tight_layout()
    plt.savefig("mosterroneouspages.png")
    plt.close()

    cursor.execute("SELECT AVG(timereq) FROM logtable;")
    avg_time_req = cursor.fetchone()[0]

    top_errors, median = wineventlog.initialize(datetime.date.today() + datetime.timedelta(days=logdays))

    credentials = exchangelib.Credentials("autoreports", "slimyFishbowls2")
    config = exchangelib.Configuration(credentials=credentials,
                                       service_endpoint="https://mail.dccabinetry.com/ews/exchange.asmx")
    account = exchangelib.Account(
        primary_smtp_address="amailer@dccabinetry.com", config=config, credentials=credentials)
    message = exchangelib.Message()

    # TODO clean this up dude lmao
    chart1 = attachments.FileAttachment(name="mosterroneouspages.png",
                                        content=open("mosterroneouspages.png", 'rb').read(),
                                        content_id="mosterroneouspages.png")

    chart2 = attachments.FileAttachment(name="requestsanderrors.png",
                                        content=open("requestsanderrors.png", 'rb').read(),
                                        content_id="requestsanderrors.png")

    chart3 = attachments.FileAttachment(name="mostviewedpages.png",
                                        content=open("mostviewedpages.png", 'rb').read(),
                                        content_id="mostviewedpages.png")

    message.attach([chart1, chart2, chart3])
    from_to = (datetime.date.today() + datetime.timedelta(days=logdays), datetime.date.today())
    # The HTML text for the message.
    txt = "<html>\n" \
          "<body>\n" \
          "From " + from_to[0].isoformat() + " through " + from_to[1].isoformat() + ", the server processed " + \
          str(total_requests) + " requests; " + str(total_errors) + \
          " (%" + str(((total_errors / total_requests) * 100.0).__round__(2)) + ") of which responded with an error.<br>" \
          "On average, it took about " + str(avg_time_req.__round__(3)) + " milliseconds to respond to requests.<br>" \
          "<img src=\"cid:requestsanderrors.png\"><br>" \
          "The top 20 most requested pages were:" \
          "<ol>"

    for page in most_requested_pages.items():
        txt += "<li>" + page[0] + " (" + str(page[1]) + " requests)</li>"

    txt += "</ol>" \
           "<img src=\"cid:mostviewedpages.png\"><br>" \
           "The top 20 pages which returned the most errors were:" \
           "<ol>"
    for page in errors_by_page.items():
        txt += "<li>" + page[0] + " (" + str(page[1]) + " errors)</li>"

    txt += "</ol>" \
           "<img src=\"cid:mosterroneouspages.png\"><br>" \
           "<b>Some of the most common error/warning event messages were:</b><br>" \
           "<small><i>These events occurred more than the median number of occurrences for all error/warning events" \
           " gathered from the Windows Event Manager log, which was " + str(median) + ".</small></i>" \
           "<ol>"

    for event in top_errors:
        txt += "<li>" + event[0] + " (" + str(event[1]) + " times)</li>"

    txt += "</ol><br>" \
           "<em> If you have any further questions, comments, suggestions, or would like access to the full" \
           " database file; send an email to chollinger@dccabinetry.com.</em><br>" \
           "<strong>Do not reply to this email, because you won't get a response.</strong>" \
           "</body></html>"

    message.subject = "Automated Server Report For %s to %s (Do Not Reply)" % \
                      (from_to[0].isoformat(), from_to[1].isoformat())
    message.body = exchangelib.HTMLBody(txt)

    message.account = account
    message.to_recipients = [
        exchangelib.Mailbox(email_address="chollinger@dccabinetry.com"),
        exchangelib.Mailbox(email_address="dcrain@dccabinetry.com"),
        exchangelib.Mailbox(email_address="cbancroft@dccabinetry.com")
        ]

    message.send()
