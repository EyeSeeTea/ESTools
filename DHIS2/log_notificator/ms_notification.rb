#!/usr/bin/ruby

require 'net/https'
require 'json'

ENV['http_proxy'] = 'http://openproxy.who.int:8080/'
ENV['https_proxy'] = 'http://openproxy.who.int:8080/'
uri = URI.parse("#{ARGV[0]}")
http = Net::HTTP.new(uri.host, uri.port)
http.use_ssl = true
request = Net::HTTP::Post.new(uri.request_uri, {'Content-Type' => 'application/json'})
request.body = {
    "text"     => "[*NOTIFICATOR LOG* - PROD] - #{ARGV[1]}",
}.to_json
response = http.request(request)
puts response.body
