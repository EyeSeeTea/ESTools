require 'json'
require 'active_support/core_ext/enumerable'
require 'active_support/time'
require 'togglv8'
require 'mail'
require 'optimist'
require 'pp'
require 'set'

class TogglAlerts
  SUBJECT_PREFIX = "toggl-alerts"
  EMAIL_FROM = "alerts@eyeseetea.com"

  def initialize(
      api_token:,
      email_recipients:,
      id:,
      date:,
      workspace:,
      tags:,
      projects:
  )
    @id, @date, @email_recipients = id, date, email_recipients
    @workspace, @projects, @tags = workspace, projects, tags

    @api = TogglV8::API.new(api_token)
    @reports = TogglV8::ReportsV2.new(api_token: api_token)
    @workspaces = @api.workspaces.map { |workspace| [workspace["name"], workspace["id"]] }.to_h
  end

  def self.debug(line)
    $stderr.puts(line)
  end

  def debug(*args)
    TogglAlerts.debug(*args)
  end

  def get_objects(all, names)
    all_by_name = all.map { |t| [t["name"], t["id"]] }.to_h
    names.map { |name| all_by_name.fetch(name) }
  end

  def get_summary(start_date, limit_hours)
    date, workspace, projects, tags = [@date, @workspace, @projects, @tags]
    workspace_id = @workspaces.fetch(workspace)
    @reports.workspace_id = workspace_id

    tag_ids = get_objects(@api.tags(workspace_id), tags)
    project_ids = get_objects(@api.projects(workspace_id), projects)

    # Maximum data span in toggl is one year
    span_limit = 1.year
    dates = (0..Float::INFINITY).lazy
      .map { |n| start_date + n * span_limit }
      .take_while { |_date| _date < date }
      .to_a

    values = (dates + [date + 1.day]).each_cons(2).map do |since, until0|
      until_ = until0 - 1.day
      debug("GET entries - #{since} -> #{until_} - project_ids=#{project_ids} - tags_ids=#{tag_ids}")
      entries = @reports.report("summary", "",
        :since => since,
        :until => until_,
        :tag_ids => tag_ids.join(','),
        :project_ids => project_ids.join(','),
      )

      reports_url = [
        "https://www.toggl.com/app/reports/summary/#{workspace_id}",
        "from/#{since.strftime('%Y-%m-%d')}/to/#{until_.strftime('%Y-%m-%d')}",
        projects.empty? ? nil : "projects/#{project_ids.join(',')}",
        tags.empty? ? nil : "tags/#{tag_ids.join(',')}",
      ].compact.join("/")

      hours = entries.map { |entry| entry["time"].to_f / 3600 / 1000 }.sum
      items_count = entries.flat_map { |entry| entry["items"] }.size

      {hours: hours, items_count: items_count, reports_url: reports_url}
    end

    total_hours = values.map { |value| value[:hours] }.sum
    items_count = values.map { |value| value[:items_count] }.sum
    reports_urls = values.map { |value| value[:reports_url] }.join("\n")
    current_usage_percent = ((total_hours / limit_hours) * 100).to_i
    total_hours_string = total_hours.round(2)

    debug("Get summary from #{date.strftime('%Y-%m-%d')}: " +
      "#{total_hours_string}h, limit = #{limit_hours}h, #{current_usage_percent}% consumed")

    {
      items_count: items_count,
      reports_url: reports_urls,
      limit_hours: limit_hours,
      total_hours: total_hours,
      total_hours_string: total_hours_string,
      current_usage_percent: current_usage_percent,
    }
  end

  def send_message(summary, body, subject)
    to = @email_recipients
    debug("Send email: #{subject} -> #{to}")
    full_body = "
      #{body}

      Workspace: #{@workspace}
      Projects: #{@projects.join(" + ").presence || "-"}
      Tags: #{@tags.join(" + ").presence || "-"}
      Entries: #{summary[:items_count]} entries
      Current hours: #{summary[:total_hours_string]}h
      Hours limit: #{summary[:limit_hours]}h
      Percent consumed: #{summary[:current_usage_percent]}%

      #{summary[:reports_url]}
    ".strip.lines.map(&:strip).join("\n")

    Mail.deliver do
      from(TogglAlerts::EMAIL_FROM)
      to(to)
      subject(subject)
      body(full_body)
    end
  end

  def send_usage_info(cache, month_summary, monthly_checks_options)
    limit_hours = monthly_checks_options.fetch(:limit_hours).to_i
    debug("Current hours: #{month_summary[:total_hours_string]}h (#{month_summary[:current_usage_percent]}%)")
    usage_info_day = (@date.end_of_month - 7.days).beginning_of_week.to_date

    if @date != usage_info_day
      debug("Today is not a monthly notification day (Monday of last full week)")
    else
      if cache[:info]
        debug("Monthly usage info email already sent")
      else
        limit_reached = month_summary[:total_hours] >= limit_hours
        body = "Today is the monthly info day"
        subject = [
          "[%s: %s] [%s:monthly]" % [SUBJECT_PREFIX, @date.strftime("%Y/%m"), @id],
          limit_reached ? "- LIMIT REACHED" : nil,
          "Last week report: #{month_summary[:current_usage_percent]}% consumed",
        ].compact.join(" ")
        send_message(month_summary, body, subject)

        cache.merge(:info => true)
      end
    end
  end

  def check_monthly_thresholds(cache, month_summary, monthly_checks_options)
    limit_hours = monthly_checks_options.fetch(:limit_hours).to_i
    thresholds = monthly_checks_options.fetch(:thresholds)

    current_threshold_reached = thresholds
      .sort
      .reverse
      .find { |threshold| month_summary[:current_usage_percent] >= threshold }

    if current_threshold_reached
      debug("Threshold reached: #{current_threshold_reached}%")

      if cache[:threshold] && current_threshold_reached <= cache[:threshold]
        debug("Threshold #{current_threshold_reached}% was already notified")
      else
        limit_reached = month_summary[:total_hours] >= limit_hours
        body = "You have reached a threshold limit: #{current_threshold_reached}%"
        subject = [
          "[%s: %s] [%s:monthly]" % [SUBJECT_PREFIX, @date.strftime("%Y/%m"), @id],
          limit_reached ? "- LIMIT REACHED" : nil,
          "Threshold reached: #{current_threshold_reached}% (consumed: #{month_summary[:current_usage_percent]}%)",
        ].compact.join(" ")
        send_message(month_summary, body, subject)

        cache.merge(:threshold => current_threshold_reached)
      end
    end
  end

  def send_yearly_summary(cache, yearly_checks_options)
    limit_hours = yearly_checks_options.fetch(:limit_hours).to_i
    start_date = Date.parse(yearly_checks_options.fetch(:start_date))

    if @date != @date.end_of_month.to_date
      debug("Today is not the yearly notification day (end of month)")
    else
      if cache[:year_summary]
        debug("Yearly summary for this month already sent")
      else
        year_summary = get_summary(start_date, limit_hours)
        limit_reached = year_summary[:total_hours] >= limit_hours
        body = "Today is the yearly summary info day"
        subject = [
          "[%s: %s] [%s:yearly]" % [SUBJECT_PREFIX, @date.strftime("%Y/%m"), @id],
          limit_reached ? "- LIMIT REACHED" : nil,
          "Last day of month: #{year_summary[:current_usage_percent]}% consumed",
        ].compact.join(" ")
        send_message(year_summary, body, subject)

        cache.merge(:year_summary => true)
      end
    end
  end

  # Cache: {"YYYY-MM" => {"threshold": VALUE, "info": BOOL}}
  def self.with_cache(cache_path, date, tasks)
    cache = File.exists?(cache_path) ? JSON.parse(File.read(cache_path)) : {}
    cache_key = date.strftime('%Y-%m')
    month_cache = (cache[cache_key] || {}).symbolize_keys

    tasks.each do |task|
      new_month_cache = task.call(month_cache)

      if new_month_cache && new_month_cache != month_cache
        new_cache = cache.merge({cache_key => new_month_cache})
        debug("Update cache: #{cache_path}")
        File.write(cache_path, JSON.pretty_generate(new_cache) + "\n")
        month_cache = new_month_cache
      end
    end
  end

  def self.run_from_options(cache_path, options = {})
    date = options.fetch(:date)
    id = options.fetch(:id)
    enabled = options.fetch(:enabled)
    full_cache_path = cache_path % id

    if !enabled
      debug("Disabled: #{id}")
    else
      debug("Run: #{id}")
      constructor_keyargs = TogglAlerts.instance_method(:initialize).parameters.map { |type, name| name }
      full_options = options.slice(*constructor_keyargs)
      alerts = TogglAlerts.new(full_options)

      with_cache(full_cache_path, date, [
          proc do |cache|
            monthly_checks_options = options[:monthly_checks]

            if monthly_checks_options && monthly_checks_options[:enabled]
              limit_hours = monthly_checks_options.fetch(:limit_hours)
              month_summary = alerts.get_summary(date.beginning_of_month, limit_hours)
              new_cache = alerts.check_monthly_thresholds(cache, month_summary, monthly_checks_options) || cache
              alerts.send_usage_info(new_cache, month_summary, monthly_checks_options) || new_cache
            end
          end,

          proc do |cache|
            yearly_checks_options = options[:yearly_checks]

            if yearly_checks_options && yearly_checks_options[:enabled]
              alerts.send_yearly_summary(cache, yearly_checks_options)
            end
          end,
      ])
    end
  end

  def self.main
    opts = Optimist::options do
      opt(:config_file, "Path to configuration file",
        type: :string,
        default: File.join(__dir__, "toggl_alerts.json"),
      )
      opt(:date, "Date month (YYYY/MM/DD)", type: :string)
    end

    $stderr.puts("Read configuration file: #{opts.config_file}")
    config = JSON.parse(File.read(opts.config_file)).deep_symbolize_keys
    date = opts[:date] ? Time.parse(opts[:date]).to_date : Date.current
    Mail.defaults { delivery_method(:smtp, config[:smtp]) }

    config[:checks].each do |check_options|
      all_options = check_options.merge(date: date)
      cache_path = File.join(File.dirname(opts.config_file), config.fetch(:cache_path))
      TogglAlerts.run_from_options(cache_path, all_options)
    end
  end
end

if __FILE__ == $0
  TogglAlerts.main
end
