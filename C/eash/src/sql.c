#define _GNU_SOURCE

#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <pwd.h>
#include <grp.h>
#include <mysql/mysql.h>
#include <mysql/mysqld_error.h>

#include "openssl/ssl.h"
#include "openssl/err.h"
#include "openssl/x509.h"
#include "openssl/rand.h"

#include "config.h"

#ifdef HAVE_CTYPE_H
#include <ctype.h>
#endif
#ifdef HAVE_SYS_IOCTL_H
#include <sys/ioctl.h>
#endif
#ifdef HAVE_SYS_SOCKET_H
#include <sys/socket.h>
#endif
#ifdef HAVE_SYS_TYPES_H
#include <sys/types.h>
#endif
#ifdef HAVE_SYS_STAT_H
#include <sys/stat.h>
#endif
#ifdef HAVE_SYS_WAIT_H
#include <sys/wait.h>
#endif
#ifdef HAVE_NETINET_IN_H
#include <netinet/in.h>
#endif
#ifdef HAVE_NETDB_H
#include <netdb.h>
#endif
#ifdef HAVE_ARPA_INET_H
#include <arpa/inet.h>
#endif
#ifdef HAVE_SYSLOG_H
#include <syslog.h>
#endif
#ifdef HAVE_SIGNAL_H
#include <signal.h>
#endif
#ifdef HAVE_SYS_TIME_H
#include <sys/time.h>
#endif

#include "servconf.h"
#include "client_id.h"
#include "ssl.h"
#include "socket.h"
#include "sig.h"
#include "log.h"
#include "sql.h"

#include "../sqlite/sqlite3.h"

    MYSQL m_conn;  
    MYSQL_RES * m_res;  
    MYSQL_ROW m_row;  

    int m_IsConnect;  
    int m_num_field;  
    int m_num_count;  

    char *m_IP;
    char *m_user;
    char *m_pass;
    char *m_db;
    int m_portdb;

void init_MysqlQi(char * IP,char * user,char * pass,char * db,int port)
{
    m_IsConnect = 0;
    m_num_field = 0;
    m_num_count = 0;
    m_res = NULL;
    
    m_IP=IP;
    m_user=user;
    m_pass=pass;
    m_db=db;
    m_portdb=port;
}

int ConnectDB()
{
    int i;

    if(m_IsConnect==1)
    {
        s_log(eINFO,"Database already connected!\n");
        return 0;
    }
    
    if(!mysql_init(&m_conn))
    {
        s_log(eERROR,"mysql_init is err!\n");
        return -1;
    }

    for(i=1;i<=3;i++)
    {
        if(mysql_real_connect(&m_conn,m_IP,m_user,m_pass,m_db,m_portdb,NULL,0))
        {
            m_IsConnect = 1;
            break;
        }
        else
        {
            s_log(eERROR,"mysql_real_connect failed to try to connect at %d times and msg:%s\n",i,mysql_error(&m_conn));
            return -1;
        }
    }
    
    if(m_IsConnect==0)
    {
        s_log(eERROR,"Connect failed to connect to mysql server!\n");
        return -1;
    }
    return 0;
}

void DisConnectDB()
{
    if(m_IsConnect==0)
    {
        s_log(eINFO,"Disconnect already disconnect;\n");
        return;
    }
    
    FreeResult();
    mysql_close(&m_conn);
    m_IsConnect=0;
}

int Reconnect()
{
	s_log(eINFO,"mysql reconnect begin ...");
	DisConnectDB();
	int i;

	    if(!mysql_init(&m_conn))
	    {
	        s_log(eERROR,"mysql_init is err!\n");
	        return -1;
	    }
     for(i=1;i<=3;i++)
     {
	    if(mysql_real_connect(&m_conn,m_IP,m_user,m_pass,m_db,m_portdb,NULL,0))
	    {
            m_IsConnect = 1;
            break;
	    }
            else
            {
            	s_log(eERROR,"mysql_real_connect failed to reconnect at %d times and msg:%s\n",i,mysql_error(&m_conn));
            	return -1;
            }
    }
	s_log(eINFO,"mysql reconnect seccess!");
	return 0;
}

void FreeResult()
{
    if(m_res)
    {
        mysql_free_result(m_res);
        m_num_field = 0;
        m_num_count = 0;
        m_res = NULL;
    }
}

int ExecSQL(char *sqlStr)
{
    if(m_IsConnect==0)
    {
        if(ConnectDB()==-1)
        {
        s_log(eERROR,"ExecSQL disconnected and failed to connect!\n");
        return -1;
        }
    }
    
    if(mysql_query(&m_conn,sqlStr))
    {
        // 错误：2006 (CR_SERVER_GONE_ERROR)消息：MySQL服务器不可用。错误：2013 (CR_SERVER_LOST)消息：查询过程中丢失了与MySQL服务器的连接。
        int e_no=mysql_errno(&m_conn);
	if(2006 == e_no||2013 == e_no)
	{
		if(Reconnect()==-1)
		{
			s_log(eERROR,"exec failed to try reconnect!");
			return -1;
		}
		if(mysql_query(&m_conn,sqlStr))
		{
                        s_log(eERROR,"execute failed <%s> again and msg <%d:%s>\n",sqlStr,mysql_errno(&m_conn), mysql_error(&m_conn));
			return -1;		
		}
	}
	else
	{
        s_log(eERROR,"execute failed <%s> and msg <%d:%s>\n",sqlStr,mysql_errno(&m_conn), mysql_error(&m_conn));
	}
    }    
    return 0;
}

int StoreResult()
{
    if(m_IsConnect == 0)
    {
        return -1;
    }

    FreeResult();

    m_res = mysql_store_result(&m_conn);
    if(m_res)
    {
        m_num_field = mysql_num_fields(m_res);
        m_num_count = mysql_num_rows(m_res);
        return 0;
    }
    else
    {
        return -1;
    }
}

int GetInsertRow()
{
    if(m_IsConnect == 0)
    {
        return -1;
    }
    if(!m_res)
    {
        return -1;
    }

    m_row = mysql_fetch_row(m_res);
    int b;
    b=atoi(m_row[0]);
    return b;
}

int stmt_mysql(char *query,char *buf,int bufsize)
{
	MYSQL_STMT * stmt;
	MYSQL_BIND params[1];
	int i;
	if(!(stmt =mysql_stmt_init(&m_conn)))
	{
    		s_log(eERROR,"mysql_stmt_init(),out of memory!");
    		return (-1);
	}
	if(i=mysql_stmt_prepare(stmt,query,strlen(query))!=0)
	 {
	        int e_no=mysql_errno(&m_conn);
		if(2006 == e_no||2013 == e_no)
                {
                        if(Reconnect()==-1)
                        {
                        s_log(eERROR,"exec failed to try reconnect!");
                        return -1;
                        }

			if(mysql_stmt_close(stmt))
			{
				s_log(eERROR,"mysql_stmt_close() failed: %s",mysql_stmt_error(stmt));
			}
			if(!(stmt =mysql_stmt_init(&m_conn)))
			{
		    		s_log(eERROR,"mysql_stmt_init(),out of memory!");
		    		return (-1);
			}
                        if(i=mysql_stmt_prepare(stmt,query,strlen(query))!=0)
                        {

                        s_log(eERROR,"mysql_stmt_prepare: %s", mysql_error(&m_conn));
                        return (-1);
                        }

                }
                else
                {
                        s_log(eERROR,"mysql_stmt_prepare: %s", mysql_error(&m_conn));
                        return (-1);
                }
        }
	memset(params,'\0',sizeof(params));

	params[0].buffer_type = MYSQL_TYPE_BLOB;
	params[0].buffer = buf;
	params[0].buffer_length = bufsize;

	if(mysql_stmt_bind_param(stmt, params))
	{
		s_log(eERROR,"mysql_stmt_bind_param() failed: %s",mysql_stmt_error(stmt));
	return (-1);
	}

	if(mysql_stmt_execute(stmt))
	{
		s_log(eERROR,"mysql_stmt_execute() failed: %s",mysql_stmt_error(stmt));
                return (-1);
	}
	if(mysql_stmt_close(stmt))
	{
		s_log(eERROR,"mysql_stmt_close() failed: %s",mysql_stmt_error(stmt));
	}

	return (0);
}

int sql_init_db(const char *file)
{
	sqlite3 *db;
	sqlite3_stmt *statement;
	int count = -1;
	char *TABLE_USER =
"CREATE TABLE USER\n"
"(\n"
" id     INTEGER PRIMARY KEY AUTOINCREMENT,\n"
" real_uid     INTEGER NOT NULL,\n"
" real_gid     INTEGER NOT NULL,\n"
" effective_uid   INTEGER NOT NULL,\n"
" effective_gid   INTEGER NOT NULL,\n"
" original_uid   INTEGER NOT NULL,\n"
" original_gid   INTEGER NOT NULL,\n"
" port   INTEGER NOT NULL,\n"
" duration     INTEGER NOT NULL,\n"
" real_pw_name   VARCHAR(63) NOT NULL,\n"
" real_gr_name   VARCHAR(63) NOT NULL,\n"
" effective_pw_name      VARCHAR(63) NOT NULL,\n"
" effective_gr_name      VARCHAR(63) NOT NULL,\n"
" original_pw_name       VARCHAR(63) NOT NULL,\n"
" original_gr_name       VARCHAR(63) NOT NULL,\n"
" terminal     VARCHAR(63) NOT NULL,\n"
" ip     VARCHAR(16) NOT NULL,\n"
" status     VARCHAR(63) NOT NULL,\n"
" stype   VARCHAR(63) NOT NULL,\n"
" method     VARCHAR(63) NOT NULL,\n"
" cipher     VARCHAR(63) NOT NULL,\n"
" sysname     VARCHAR(63) NOT NULL,\n"
" nodename     VARCHAR(63) NOT NULL,\n"
" release     VARCHAR(63) NOT NULL,\n"
" version     VARCHAR(63) NOT NULL,\n"
" machine     VARCHAR(63) NOT NULL,\n"
" file_session   VARCHAR(63),\n"
" hash_session   VARCHAR(63),\n"
" dns    VARCHAR(127),\n"
" remote_command     VARCHAR(255),\n"
" pid     INTEGER NOT NULL,\n"
" created      DATETIME,\n"
" modified     DATETIME\n"
");\n"
"\n"
"CREATE TRIGGER INSERT_USER_CREATED AFTER INSERT ON USER\n"
"BEGIN\n"
" UPDATE USER SET created = DATETIME('now', 'localtime') WHERE id = new.id;\n"
" UPDATE USER SET modified = DATETIME('now', 'localtime') WHERE id = new.id;\n"
"END;\n"
"\n"
"CREATE TRIGGER INSERT_USER_MODIFIED AFTER UPDATE ON USER\n"
"BEGIN\n"
" UPDATE USER SET modified = DATETIME('now', 'localtime') WHERE id = new.id;\n"
"END;";

	if(sqlite3_open(file, &db))
	{
		s_log(eERROR, "sqlite3_open(%.100s): %.100s", file, sqlite3_errmsg(db));
		sqlite3_close(db);
		return(-1);
	}

	if(sqlite3_prepare(db, "SELECT COUNT(*) FROM sqlite_master WHERE name=? AND type=?;", -1, &statement, NULL) != SQLITE_OK)
	{
		s_log(eERROR, "sqlite3_prepare: %.100s", sqlite3_errmsg(db));
		sqlite3_close(db);
		return(-1);
	}

	sqlite3_bind_text(statement, 1, "USER", -1, SQLITE_TRANSIENT);
	sqlite3_bind_text(statement, 2, "table", -1, SQLITE_TRANSIENT);

	sqlite3_busy_timeout(db, 2000);

	switch(sqlite3_step(statement))
	{
		case SQLITE_ROW:
			count = sqlite3_column_int(statement, 0);
			break;
		case SQLITE_DONE:
			break;
		default:
			s_log(eERROR, "sqlite3_step: %.100s", sqlite3_errmsg(db));
			break;
	}

	sqlite3_finalize(statement);

	if(count <= 0)
	{
		s_log(eINFO, "sqlite3: creating table 'USER'");
		switch(sqlite3_exec(db, TABLE_USER, NULL, NULL, NULL))
		{
			case SQLITE_OK:
				break;
			default:
				s_log(eERROR, "sqlite3_exec: %.100s", sqlite3_errmsg(db));
				break;
		}
	}
	else
	{
		s_log(eDEBUG1, "table USER found");
		sqlite3_close(db);

		if(chmod(file, 0600) < 0)
		{
			s_log(eERROR, "chmod(%.100s, 0600): %.100s (%i)", file, strerror(errno), errno);
			return(-1);
		}

		return(1);
	}

	sqlite3_close(db);

	if(chmod(file, 0600) < 0)
	{
		s_log(eERROR, "chmod(%.100s, 0600): %.100s (%i)", file, strerror(errno), errno);
		return(-1);
	}

	return(0);
}
