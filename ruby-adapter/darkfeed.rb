#!/usr/bin/ruby
#DarkFeed.io Adapter (Ruby)
#Mauro Eldritch @ DarkFeed - 2023
require_relative 'config.rb'
require 'terminal-table' if $output_format == "table"
require 'colorize'
require 'curb'
require 'json'
require 'pdfkit'

def banner()
    banner = '''
     _____             _    ______            _   _       
    |  __ \           | |  |  ____|          | | (_)      
    | |  | | __ _ _ __| | _| |__ ___  ___  __| |  _  ___  
    | |  | |/ _| | ,__| |/ /  __/ _ \/ _ \/ _  | | |/ _ \ 
    | |__| | (_| | |  |   <| | |  __/  __/ (_| |_| | (_) |
    |_____/ \__,_|_|  |_|\_\_|  \___|\___|\__,_(_)_|\___/ 
                                    Ruby Adapter v1.00
    '''
    puts banner.light_red
end

def initial_connection()
    #Check desired output format
    if ['text', 'json', 'table', 'csv', 'yaml', 'pdf'].include? $output_format
        puts "[*] Output format: #{$output_format}.".light_blue
    else
        puts "[!] Unknown output format. Defaulting to JSON.".light_yellow
        $output_format = "json"
    end

    #Check authentication cookie
    if $cookie.empty?
        puts "[x] Authentication cookie is not set. Please place your cookie in the config.rb file.".light_red
        exit(1)
    else
        puts "[*] Authentication cookie found. Attempting connection...".light_blue
    end

    #Fetch latest posts
    http = Curl.get("https://darkfeed.io/wp-json/wp/v2/posts") do |http|
        http.headers['Cookie'] = "#{$cookie}"
    end
    json_results = JSON.parse(http.body)
    final_output = ""

    #Determine subscription level
    if json_results.count == 10
        puts "[*] Subscription plan: Free.".light_blue
    elsif json_results.count > 10
        puts "[*] Subscription plan: Premium.".light_blue
    end
    puts "[*] Available results: #{json_results.count}.".light_blue
    
    #Parse retrieved intelligence using defined format
    case $output_format
    when "json"
        final_output = json_results
    when "table"
        rows = []
        json_results.each do | result |
            rows << [result['title']['rendered'], result['date'], result['link'], result['jetpack_featured_media_url'].split("?")[0]]
        end
        final_output = Terminal::Table.new :headings => ['Actor', 'Date', 'Link', 'Screenshot'], :rows => rows
    when "text"
        json_results.each do | result |
            final_output += "Actor:\t#{result['title']['rendered']}\n"
            final_output += "Date:\t#{result['date']}\n"
            final_output += "Link:\t#{result['link']}\n"
            final_output += "Media:\t#{result['jetpack_featured_media_url'].split("?")[0]}\n\n"
        end
    when "csv"
        final_output += "Actor,Date,Link,Media\n"
        json_results.each do | result |
            final_output += "#{result['title']['rendered']},#{result['date']},#{result['link']},#{result['jetpack_featured_media_url'].split("?")[0]}\n"
        end
    when "yaml"
        final_output += "- incidents:\n"
        json_results.each do | result |
            final_output += "\t- {actor: \"#{result['title']['rendered']}\", date: \"#{result['date']}\", link: \"#{result['link']}\", media: \"#{result['jetpack_featured_media_url'].split("?")[0]}\"}\n"
        end
    when "pdf"
        $output_channel = "file"
        html_template = File.read("../report-templates/report_template.html")
        final_output += html_template.split("<!--CUT-HERE-PLACEHOLDER-->")[0]
        json_results.each do | result |
            final_output += "<tr><td>#{result['title']['rendered']}</td><td>#{result['date']}</td><td>#{result['link']}</td><td>#{result['jetpack_featured_media_url'].split("?")[0]}</td></tr>\n"
        end          
        final_output += html_template.split("<!--CUT-HERE-PLACEHOLDER-->")[1]
        File.write("../report-templates/report.html", "#{final_output}")
    end

    #Output intelligence using defined channel
    case $output_channel
    when "stdout"
        puts "[>] Retrieved intelligence:".light_blue
        puts "\n#{final_output}"
    when "file"
        if $output_format == "pdf"
            html_template = File.read("../report-templates/report.html")
            kit = PDFKit.new(html_template)
            pdf = kit.to_pdf
            file = kit.to_file("./darkfeed_output.pdf")
            File.delete("../report-templates/report.html")
            puts "[*] Output written to darkfeed_output.pdf.".light_blue
        else
            File.write('darkfeed_output.txt', "#{final_output}")
            puts "[*] Output written to darkfeed_output.txt.".light_blue
        end
    end
end

banner()
initial_connection()