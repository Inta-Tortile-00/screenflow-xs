package org.example.screenflow;

import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.os.*;
import java.util.*;

public class RotationService extends Service {
    static final String PKG="org.jwz.android.xscreensaver", CHANNEL="screenflow_rotation";
    static final int ID=4822;
    final Handler handler=new Handler(Looper.getMainLooper());
    final ArrayList<String> queue=new ArrayList<>();
    SharedPreferences prefs;
    String current="";
    long interval=30000, count=0, due=0;
    boolean paused=false;
    final Runnable tick=()->advance();
    public IBinder onBind(Intent i){return null;}
    public void onCreate(){super.onCreate(); prefs=getSharedPreferences("rotation",0);
        NotificationManager nm=getSystemService(NotificationManager.class);
        nm.createNotificationChannel(new NotificationChannel(CHANNEL,"ScreenFlow rotation",NotificationManager.IMPORTANCE_LOW));
        interval=prefs.getLong("interval",30000); count=prefs.getLong("count",0); current=prefs.getString("current",""); paused=prefs.getBoolean("paused",false);
        String saved=prefs.getString("queue",""); if(!saved.isEmpty()) Collections.addAll(queue,saved.split("\n"));
    }
    void save(){prefs.edit().putLong("interval",interval).putLong("count",count).putString("current",current).putString("queue",android.text.TextUtils.join("\n",queue)).putBoolean("paused",paused).apply();}
    PendingIntent action(String a,int n){return PendingIntent.getService(this,n,new Intent(this,RotationService.class).setAction(a),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);}
    Notification notification(){
        Notification.Builder b=new Notification.Builder(this,CHANNEL).setSmallIcon(android.R.drawable.ic_menu_gallery).setOngoing(true).setOnlyAlertOnce(true);
        String name=current.isEmpty()?"No module selected":current.substring(current.lastIndexOf('$')+1);
        b.setContentTitle("ScreenFlow XS: "+name).setContentText((paused?"Paused":"Selection pending confirmation")+" · #"+count+" · "+interval/1000+"s interval");
        if(!current.isEmpty()){
            Intent picker=new Intent(WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER).putExtra(WallpaperManager.EXTRA_LIVE_WALLPAPER_COMPONENT,new ComponentName(PKG,current));
            PendingIntent p=PendingIntent.getActivity(this,1,picker,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
            b.setContentIntent(p).addAction(android.R.drawable.ic_menu_view,"Apply",p);
        }
        b.addAction(android.R.drawable.ic_media_next,"Next",action("NEXT",2));
        b.addAction(android.R.drawable.ic_media_pause,paused?"Resume":"Pause",action("PAUSE",3));
        b.addAction(android.R.drawable.ic_menu_close_clear_cancel,"Stop",action("STOP",4));
        return b.build();
    }
    void schedule(){handler.removeCallbacks(tick); if(!paused){due=SystemClock.elapsedRealtime()+interval;handler.postDelayed(tick,interval);} }
    void advance(){
        if(queue.isEmpty()){
            Intent q=new Intent("android.service.wallpaper.WallpaperService").setPackage(PKG);
            for(ResolveInfo r:getPackageManager().queryIntentServices(q,0)) if(r.serviceInfo.exported && r.serviceInfo.enabled) queue.add(r.serviceInfo.name);
            Collections.shuffle(queue); if(queue.size()>1 && queue.get(0).equals(current)) Collections.swap(queue,0,1);
        }
        if(!queue.isEmpty()){current=queue.remove(0);count++;} else current="";
        save(); getSystemService(NotificationManager.class).notify(ID,notification()); schedule();
    }
    public int onStartCommand(Intent i,int flags,int startId){
        String a=i==null?"RESTORE":i.getAction();
        if("STOP".equals(a)){prefs.edit().putBoolean("running",false).apply();handler.removeCallbacks(tick);stopForeground(true);stopSelf();return START_NOT_STICKY;}
        if("START".equals(a)){interval=Math.max(1000,Math.min(86400000,i.getIntExtra("interval",30000)));paused=false;}
        if("PAUSE".equals(a))paused=!paused;
        prefs.edit().putBoolean("running",true).apply();save();startForeground(ID,notification());
        if("NEXT".equals(a)||current.isEmpty())advance();else schedule();
        return START_STICKY;
    }
    public void onDestroy(){handler.removeCallbacks(tick);super.onDestroy();}
}
