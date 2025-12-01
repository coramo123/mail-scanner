-- User Subscriptions Schema for Mail Scanner
-- Run this SQL in your Supabase SQL Editor after setting up the main schema

-- Create user_subscriptions table
create table if not exists user_subscriptions (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references auth.users(id) on delete cascade not null unique,

  -- Plan information
  plan_type text not null default 'free' check (plan_type in ('free', 'starter', 'growth', 'scale', 'enterprise')),
  status text not null default 'active' check (status in ('active', 'cancelled', 'past_due', 'incomplete')),

  -- Stripe information
  stripe_customer_id text,
  stripe_subscription_id text,
  stripe_price_id text,

  -- Billing period
  current_period_start timestamp with time zone,
  current_period_end timestamp with time zone,

  -- Usage tracking
  scans_this_month integer default 0 not null,
  total_scans integer default 0 not null,
  last_scan_at timestamp with time zone,

  -- Metadata
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null
);

-- Create index on user_id for faster lookups
create index if not exists user_subscriptions_user_id_idx on user_subscriptions(user_id);

-- Create index on stripe_customer_id for webhook processing
create index if not exists user_subscriptions_stripe_customer_idx on user_subscriptions(stripe_customer_id);

-- Enable Row Level Security
alter table user_subscriptions enable row level security;

-- RLS Policies
-- Users can view their own subscription
create policy "Users can view their own subscription"
  on user_subscriptions
  for select
  using (auth.uid() = user_id);

-- Users can insert their own subscription (on signup)
create policy "Users can insert their own subscription"
  on user_subscriptions
  for insert
  with check (auth.uid() = user_id);

-- Users can update their own subscription
create policy "Users can update their own subscription"
  on user_subscriptions
  for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Create trigger to update updated_at timestamp
create trigger update_user_subscriptions_updated_at
  before update on user_subscriptions
  for each row
  execute function update_updated_at_column();

-- Function to reset monthly scan counts (call this monthly via cron)
create or replace function reset_monthly_scans()
returns void as $$
begin
  update user_subscriptions
  set scans_this_month = 0
  where current_period_end < now()
    and status = 'active';
end;
$$ language plpgsql security definer;

-- Function to check if user can scan (respects plan limits)
create or replace function can_user_scan(p_user_id uuid)
returns boolean as $$
declare
  v_subscription record;
  v_scan_limit integer;
begin
  -- Get user subscription
  select * into v_subscription
  from user_subscriptions
  where user_id = p_user_id;

  -- If no subscription, create free tier
  if v_subscription is null then
    insert into user_subscriptions (user_id, plan_type, status)
    values (p_user_id, 'free', 'active')
    returning * into v_subscription;
  end if;

  -- Determine scan limit based on plan
  case v_subscription.plan_type
    when 'free' then v_scan_limit := 100;
    when 'starter' then v_scan_limit := 1000;
    when 'growth' then v_scan_limit := 3000;
    when 'scale' then v_scan_limit := 10000;
    when 'enterprise' then v_scan_limit := 999999; -- Effectively unlimited
    else v_scan_limit := 0;
  end case;

  -- Check if under limit
  return v_subscription.scans_this_month < v_scan_limit;
end;
$$ language plpgsql security definer;

-- Function to increment scan count
create or replace function increment_scan_count(p_user_id uuid)
returns void as $$
begin
  update user_subscriptions
  set
    scans_this_month = scans_this_month + 1,
    total_scans = total_scans + 1,
    last_scan_at = now(),
    updated_at = now()
  where user_id = p_user_id;

  -- Create subscription if it doesn't exist
  if not found then
    insert into user_subscriptions (user_id, plan_type, scans_this_month, total_scans, last_scan_at)
    values (p_user_id, 'free', 1, 1, now());
  end if;
end;
$$ language plpgsql security definer;

-- Grant access to authenticated users
grant usage on schema public to authenticated;
grant all on user_subscriptions to authenticated;

-- Create default subscription for existing users
insert into user_subscriptions (user_id, plan_type, status)
select id, 'free', 'active'
from auth.users
where id not in (select user_id from user_subscriptions)
on conflict (user_id) do nothing;
