require 'json'
require 'active_support/core_ext/enumerable'
require 'active_support/time'
require 'togglv8'
require 'mail'
require 'optimist'
require 'pp'

class TogglAlerts
  SUBJECT_PREFIX = "toggl-alarms"

  def initialize(
      api_token:,
      cache_path:,
      limit_hours:,
      date:,
      workspace:,
      email_recipients:,
      email_from:,
      tag: nil,
      project: nil,
      thresholds: nil
  )
    @date, @cache_path, @limit_hours = date, cache_path, limit_hours
    @email_from, @email_recipients, @thresholds = email_from, email_recipients, thresholds
    @workspace, @project, @tag = workspace, project, tag

    @api = TogglV8::API.new(api_token)
    @reports = TogglV8::ReportsV2.new(api_token: api_token)
    @workspaces = @api.workspaces.map { |workspace| [workspace["name"], workspace["id"]] }.to_h
    @summary = get_summary_for_month
  end

  def debug(line)
    $stderr.puts(line)
  end

  def get_summary_for_month
    date, workspace, project, tag = [@date, @workspace, @project, @tag]
    workspace_id = @workspaces.fetch(workspace)
    @reports.workspace_id = workspace_id

    tag_id = tag ? @api.tags(workspace_id).map { |t| [t["name"], t["id"]] }.to_h.fetch(tag) : ""
    project_id = project ? @api.projects(workspace_id).map { |p| [p["name"], p["id"]] }.to_h.fetch(project) : ""

    entries = @reports.report("summary", "",
      :since => date.beginning_of_month,
      :until => date,
      :tag_ids => tag_id.to_s,
      :project_ids => project_id.to_s,
    )

    reports_url = [
      "https://www.toggl.com/app/reports/summary/#{workspace_id}",
      "from/#{date.beginning_of_month.strftime('%Y-%m-%d')}/to/#{date.strftime('%Y-%m-%d')}",
      project && "projects/#{project_id}",
      tag && "tags/#{tag_id}",
    ].compact.join("/")

    total_hours = entries.map { |entry| entry["time"].to_f / 3600 / 1000 }.sum

    {
      items: entries.flat_map { |entry| entry["items"] },
      reports_url: reports_url,
      total_hours: total_hours,
      total_hours_string: total_hours.round(2),
      current_usage_percent: ((total_hours / @limit_hours) * 100).to_i,
    }
  end

  def send_message(body, subject)
    email_from = @email_from
    to = @email_recipients
    debug("Send email: #{subject} -> #{to}")
    full_body = "
      #{body}

      Workspace: #{@workspace}
      Project: #{@project || "-"}
      Tag: #{@tag  || "-"}
      Total items in month: #{@summary[:items].size}
      Total current month hours: #{@summary[:total_hours_string]}
      Hours limit: #{@limit_hours}
      Percent consumed: #{@summary[:current_usage_percent]}%

      #{@summary[:reports_url]}
    ".strip.lines.map(&:strip).join("\n")

    Mail.deliver do
      from(email_from)
      to(to)
      subject(subject)
      body(full_body)
    end
  end

  # Cache: {"YYYY-MM" => {"threshold": VALUE, "info": BOOL}}
  def with_cache(cache_path)
    cache = File.exists?(cache_path) ? JSON.parse(File.read(cache_path)) : {}
    cache_key = @date.strftime('%Y-%m')
    month_cache = (cache[cache_key] || {}).symbolize_keys
    new_month_cache = yield(month_cache)

    if new_month_cache != month_cache
      new_cache = cache.merge({cache_key => new_month_cache})
      debug("Update cache: #{cache_path}")
      File.write(cache_path, JSON.pretty_generate(new_cache) + "\n")
    end
  end

  def check_thresholds(cache)
    current_threshold_reached = (@thresholds || "")
      .sort
      .reverse
      .find { |threshold| @summary[:current_usage_percent] >= threshold }

    if current_threshold_reached
      debug("Threshold reached: #{current_threshold_reached}%")

      if cache[:threshold] && current_threshold_reached <= cache[:threshold]
        debug("Threshold #{current_threshold_reached}% was already notified")
      else
        body = "You have reached a threshold limit: #{current_threshold_reached}%"
        subject = [
          "[%s: %s]" % [SUBJECT_PREFIX, @date.beginning_of_month.strftime("%Y/%m")],
          "Limit reached: #{current_threshold_reached}% (consumed: #{@summary[:current_usage_percent]}%)",
        ].compact.join(" ")
        send_message(body, subject)
        cache.merge(:threshold => current_threshold_reached)
      end
    end || cache
  end

  def send_usage_info(cache)
    usage_info_day = (@date.end_of_month - 7.days).beginning_of_week.to_date

    if @date == usage_info_day
      if cache[:info]
        debug("Montly usage info email already sent")
      else
        limit_reached = @summary[:total_hours] >= @limit_hours
        body = "Today is the monthly info day"
        subject = [
          "[%s: %s]" % [SUBJECT_PREFIX, @date.beginning_of_month.strftime("%Y/%m")],
          "Last week of month: #{@summary[:current_usage_percent]}% consumed",
          limit_reached ? "- WARNING: LIMIT REACHED" : nil,
        ].compact.join(" ")
        send_message(body, subject)
        cache.merge(:info => true)
      end
    end || cache
  end

  def notify
    debug("Current hours: #{@summary[:total_hours_string]}h (#{@summary[:current_usage_percent]}%)")

    with_cache(@cache_path) do |cache|
      check_thresholds(send_usage_info(cache))
    end
  end
end

if __FILE__ == $0
  opts = Optimist::options do
    opt(:config_file, "Path to configuration file",
      type: :string,
      default: File.join(__dir__, "toggl_alerts.json"),
    )
    opt(:date, "Date month (YYYY/MM/DD)", type: :string)
  end

  $stderr.puts("Read configuration file: #{opts.config_file}")
  all_options = JSON.parse(File.read(opts.config_file)).symbolize_keys.merge({
    date: opts[:date] ? Time.parse(opts[:date]).to_date : Date.current,
  })
  $stderr.puts("Options: " + all_options.pretty_inspect)
  alerts = TogglAlerts.new(all_options)
  alerts.notify
end
