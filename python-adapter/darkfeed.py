#!/usr/bin/python
#DarkFeed.io Adapter (Python)
#Mauro Eldritch @ DarkFeed - 2023
import config
from pathlib import Path
from termcolor import colored
import json
import requests
from prettytable import PrettyTable
import pdfkit

def banner():
    banner = '''
     _____             _    ______            _   _       
    |  __ \           | |  |  ____|          | | (_)      
    | |  | | __ _ _ __| | _| |__ ___  ___  __| |  _  ___  
    | |  | |/ _| | ,__| |/ /  __/ _ \/ _ \/ _  | | |/ _ \ 
    | |__| | (_| | |  |   <| | |  __/  __/ (_| |_| | (_) |
    |_____/ \__,_|_|  |_|\_\_|  \___|\___|\__,_(_)_|\___/ 
                                    Python Adapter v1.00
    '''
    print(colored(banner, "blue"))

def initial_connection():
    #Check desired output format
    if config.output_format in ['text', 'json', 'table', 'csv', 'yaml', 'pdf']:
        print(colored("[*] Output format: "+ str(config.output_format) +".", "blue"))
    else:
        print(colored("[!] Unknown output format. Defaulting to JSON.", "yellow"))
        config.output_format = "json"

    #Check authentication cookie
    if config.cookie:
        print(colored("[*] Authentication cookie found. Attempting connection...", "blue"))
    else:
        print(colored("[x] Authentication cookie is not set. Please place your cookie in the config.rb file.", "red"))
        exit(1)        

    #Fetch latest posts
    url = 'https://darkfeed.io/wp-json/wp/v2/posts'
    cookies = {config.cookie.split("=")[0] : config.cookie.split("=")[1]}
    r = requests.get(url, cookies=cookies)
    json_results = r.json()
    final_output = ""

    #Determine subscription level
    if len(json_results) == 10:
        print(colored("[*] Subscription plan: Free.", "blue"))
    elif json_results.count > 10:
        print(colored("[*] Subscription plan: Premium.", "blue"))
    print(colored("[*] Available results: "+ str(len(json_results)) +".", "blue"))

    #Parse retrieved intelligence using defined format
    if config.output_format == "json":
        final_output = json_results
    elif config.output_format == "table":
        t = PrettyTable(['Actor', 'Date', 'Link', 'Screenshot'])
        for result in json_results:
            t.add_row([result['title']['rendered'], result['date'], result['link'], result['jetpack_featured_media_url'].split("?")[0]])
        final_output = t
    elif config.output_format == "text":
        for result in json_results:
            final_output += "Actor:\t"+ result['title']['rendered'] +"\n"
            final_output += "Date:\t"+ result['date'] +"\n"
            final_output += "Link:\t"+ result['link'] +"\n"
            final_output += "Media:\t"+ result['jetpack_featured_media_url'].split("?")[0] +"\n\n"
    elif config.output_format == "csv":
        final_output += "Actor,Date,Link,Media\n"
        for result in json_results:
            final_output += result['title']['rendered'] +","+ result['date'] +","+ result['link'] +","+ result['jetpack_featured_media_url'].split("?")[0] +"\n"
    elif config.output_format == "yaml":
        final_output += "- incidents:\n"
        for result in json_results:
            final_output += "\t- {actor: \"" + result['title']['rendered'] +"\", date: \""+ result['date']+ "\", link: \""+ result['link'] +"\", media: \""+ result['jetpack_featured_media_url'].split("?")[0] +"\"}\n"
    elif config.output_format == "pdf":
        config.output_channel = "file"
        html_template = Path("../report-templates/report_template.html").read_text()
        final_output += html_template.split("<!--CUT-HERE-PLACEHOLDER-->")[0]
        for result in json_results:
            final_output += "<tr><td>"+ result['title']['rendered'] +"</td><td>"+ result['date'] +"</td><td>"+ result['link'] +"</td><td>"+ result['jetpack_featured_media_url'].split("?")[0] +"</td></tr>\n"
        final_output += html_template.split("<!--CUT-HERE-PLACEHOLDER-->")[1]
        Path("../report-templates/report.html").write_text(str(final_output))

    #Output intelligence using defined channel
    if config.output_channel == "stdout":
        print(colored("[>] Retrieved intelligence:", "blue"))
        print("\n"+ str(final_output))
    elif config.output_channel == "file":
        if config.output_format == "pdf":
            pdfkit.from_file('../report-templates/report.html', './darkfeed_output.pdf')
            Path('../report-templates/report.html').unlink()
            print(colored("[*] Output written to darkfeed_output.pdf.", "blue"))
        else:
            Path("darkfeed_output.txt").write_text(str(final_output))
            print(colored("[*] Output written to darkfeed_output.txt.", "blue"))

banner()
initial_connection()