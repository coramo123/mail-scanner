-- Mail Scanner Database Schema for Supabase
-- Run this SQL in your Supabase SQL Editor: https://supabase.com/dashboard/project/_/sql

-- Enable UUID extension (if not already enabled)
create extension if not exists "uuid-ossp";

-- Create scan_results table
create table if not exists scan_results (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references auth.users(id) on delete cascade not null,

  -- Original uploaded file info
  filename text not null,
  uploaded_at timestamp with time zone default now() not null,

  -- Extracted address information
  sender_name text,
  street text,
  city text,
  state text,
  zip text,
  full_address text,
  category text,
  method text,

  -- Smarty verification results
  verified boolean default false,
  verification_status text,
  verified_street text,
  verified_city text,
  verified_state text,
  verified_zip text,
  verified_full_address text,

  -- Metadata
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null
);

-- Create index on user_id for faster queries
create index if not exists scan_results_user_id_idx on scan_results(user_id);

-- Create index on uploaded_at for sorting
create index if not exists scan_results_uploaded_at_idx on scan_results(uploaded_at desc);

-- Enable Row Level Security (RLS)
alter table scan_results enable row level security;

-- Create RLS policies
-- Policy: Users can only view their own scan results
create policy "Users can view their own scan results"
  on scan_results
  for select
  using (auth.uid() = user_id);

-- Policy: Users can insert their own scan results
create policy "Users can insert their own scan results"
  on scan_results
  for insert
  with check (auth.uid() = user_id);

-- Policy: Users can update their own scan results
create policy "Users can update their own scan results"
  on scan_results
  for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Policy: Users can delete their own scan results
create policy "Users can delete their own scan results"
  on scan_results
  for delete
  using (auth.uid() = user_id);

-- Create a function to automatically update the updated_at timestamp
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- Create trigger to automatically update updated_at
create trigger update_scan_results_updated_at
  before update on scan_results
  for each row
  execute function update_updated_at_column();

-- Grant access to authenticated users
grant usage on schema public to authenticated;
grant all on scan_results to authenticated;
