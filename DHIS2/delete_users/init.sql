create temp table tmp_list_userids (uid varchar);
copy tmp_list_userids from '/var/lib/postgresql/data/init.csv' DELIMITER ',' CSV HEADER;

select count(*) from userinfo where creatoruserid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update userinfo set creatoruserid=(select userinfoid from userinfo where username='dev.user') where creatoruserid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));

select count(*) from fileresource where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
select count(*) from fileresource where lastupdatedby in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update fileresource set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update fileresource set lastupdatedby=(select userinfoid from userinfo where username='dev.user') where lastupdatedby in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));

select count(*) from document where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
select count(*) from document where lastupdatedby in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update document set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update document set lastupdatedby=(select userinfoid from userinfo where username='dev.user') where lastupdatedby in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
