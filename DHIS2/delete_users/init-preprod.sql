create temp table tmp_list_userids (uid varchar);
copy tmp_list_userids from '/var/lib/postgresql/preprod-only-id.csv' CSV;

select count(*) from userinfo where creatoruserid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update userinfo set creatoruserid=(select userinfoid from userinfo where username='dev.user') where creatoruserid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update userinfo set creatoruserid=(select userinfoid from userinfo where username='dev.user') where creatoruserid='10722029';
