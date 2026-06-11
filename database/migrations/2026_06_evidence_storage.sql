begin;

grant insert on public.evidencias to anon;

do $$
begin
    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'evidencias'
          and policyname = 'anon_insert_evidencias'
    ) then
        create policy anon_insert_evidencias
            on public.evidencias
            for insert
            to anon
            with check (true);
    end if;
end $$;

insert into storage.buckets (
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types
)
values (
    'evidencias',
    'evidencias',
    false,
    20971520,
    array[
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'image/png',
        'image/jpeg'
    ]
)
on conflict (id) do nothing;

do $$
begin
    if not exists (
        select 1
        from pg_policies
        where schemaname = 'storage'
          and tablename = 'objects'
          and policyname = 'anon_insert_evidencias'
    ) then
        create policy anon_insert_evidencias
            on storage.objects
            for insert
            to anon
            with check (bucket_id = 'evidencias');
    end if;

    if not exists (
        select 1
        from pg_policies
        where schemaname = 'storage'
          and tablename = 'objects'
          and policyname = 'anon_select_evidencias'
    ) then
        create policy anon_select_evidencias
            on storage.objects
            for select
            to anon
            using (bucket_id = 'evidencias');
    end if;
end $$;

commit;
