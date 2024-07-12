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

update trackedentitycomment set lastupdatedby=(select userinfoid from userinfo where username='dev.user') where lastupdatedby in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update trackedentitycomment set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update trackedentityinstance set lastupdatedby=(select userinfoid from userinfo where username='dev.user') where lastupdatedby in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update trackedentityinstance set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update trackedentityattribute set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update trackedentityattribute set lastupdatedby=(select userinfoid from userinfo where username='dev.user') where lastupdatedby in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update trackedentitytype set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update trackedentitytype set lastupdatedby=(select userinfoid from userinfo where username='dev.user') where lastupdatedby in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update keyjsonvalue set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update messageconversation set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update visualization set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update visualization set lastupdatedby=(select userinfoid from userinfo where username='dev.user') where lastupdatedby in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update categorycombo set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update programstageinstancefilter set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update programstageinstancefilter set lastupdatedby=(select userinfoid from userinfo where username='dev.user') where lastupdatedby in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update dashboard set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update dashboard set lastupdatedby=(select userinfoid from userinfo where username='dev.user') where lastupdatedby in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update dataelement set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update dataelementcategory set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update dataelementcategoryoption set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update dataelementgroup set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update dataset set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update indicator set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update optionset set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update organisationunit set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update orgunitgroup set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update program set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update programstage set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update usergroup set userid=(select userinfoid from userinfo where username='dev.user') where userid in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update usergroup set lastupdatedby=(select userinfoid from userinfo where username='dev.user') where lastupdatedby in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update dataapproval set creator=(select userinfoid from userinfo where username='dev.user') where creator in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
update dataapprovalaudit set creator=(select userinfoid from userinfo where username='dev.user') where creator in (select userinfoid from userinfo where uid in (select uid from tmp_list_userids));
