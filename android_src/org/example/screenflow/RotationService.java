package org.example.screenflow;
import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.os.*;
import java.util.*;
import java.io.*;

public class RotationService extends Service {
 static final String PKG="org.jwz.android.xscreensaver", CHANNEL="screenflow_rotation";
 static final int ID=4822;
 final Handler handler=new Handler(Looper.getMainLooper());
 final ArrayList<String> queue=new ArrayList<>(), images=new ArrayList<>();
 SharedPreferences prefs;
 String current="", lastImage="", mode="XS only", policy="Immediate", folder="", xpath=WallpaperAccessibilityService.PRIMARY, status="Waiting";
 long interval=60000, imageInterval=300000, xsDue, imageDue, count, imageCount, idle=60000;
 boolean paused, automatic, shuffle=true, wasLocked, unlockWindow, preferImage, writing;
 final Runnable tick=()->step();
 public IBinder onBind(Intent i){return null;}
 public void onCreate(){super.onCreate();prefs=getSharedPreferences("rotation",0);getSystemService(NotificationManager.class).createNotificationChannel(new NotificationChannel(CHANNEL,"ScreenFlow rotation",NotificationManager.IMPORTANCE_LOW));
 mode=prefs.getString("mode","XS only");policy=prefs.getString("policy","Immediate");folder=prefs.getString("folder","");xpath=prefs.getString("xpath",WallpaperAccessibilityService.PRIMARY);automatic=prefs.getBoolean("automatic",false);shuffle=prefs.getBoolean("shuffle",true);paused=prefs.getBoolean("paused",false);interval=prefs.getLong("interval",60000);imageInterval=prefs.getLong("imageInterval",300000);idle=prefs.getLong("idle",60000);count=prefs.getLong("count",0);imageCount=prefs.getLong("imageCount",0);current=prefs.getString("current","");lastImage=prefs.getString("lastImage","");String q=prefs.getString("queue","");if(!q.isEmpty())Collections.addAll(queue,q.split("\n"));xsDue=imageDue=SystemClock.elapsedRealtime();}
 void save(){prefs.edit().putString("mode",mode).putString("policy",policy).putString("folder",folder).putString("xpath",xpath).putBoolean("automatic",automatic).putBoolean("shuffle",shuffle).putBoolean("paused",paused).putLong("interval",interval).putLong("imageInterval",imageInterval).putLong("idle",idle).putLong("count",count).putLong("imageCount",imageCount).putString("current",current).putString("lastImage",lastImage).putString("queue",android.text.TextUtils.join("\n",queue)).apply();}
 boolean xs(){return !"Images only".equals(mode);} boolean img(){return !"XS only".equals(mode);}
 PendingIntent action(String a,int n){return PendingIntent.getService(this,n,new Intent(this,RotationService.class).setAction(a),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);}
 Notification notification(){long now=SystemClock.elapsedRealtime();String times=(xs()?"XS "+Math.max(0,(xsDue-now+999)/1000)+"s ":"")+(img()?"Images "+Math.max(0,(imageDue-now+999)/1000)+"s":"");Notification.Builder b=new Notification.Builder(this,CHANNEL).setSmallIcon(android.R.drawable.ic_menu_gallery).setOngoing(true).setOnlyAlertOnce(true).setContentTitle("ScreenFlow: "+(paused?"Paused":status)).setContentText(times+" · "+policy);if(xs()&&!current.isEmpty()&&!automatic&&!writing){Intent p=new Intent(WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER).putExtra(WallpaperManager.EXTRA_LIVE_WALLPAPER_COMPONENT,new ComponentName(PKG,current));b.addAction(android.R.drawable.ic_menu_view,"Apply",PendingIntent.getActivity(this,1,p,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE));}return b.addAction(android.R.drawable.ic_media_next,"Next",action("NEXT",2)).addAction(android.R.drawable.ic_media_pause,paused?"Resume":"Pause",action("PAUSE",3)).addAction(android.R.drawable.ic_menu_close_clear_cancel,"Stop",action("STOP",4)).build();}
 void step(){handler.removeCallbacks(tick);long now=SystemClock.elapsedRealtime();boolean locked=getSystemService(KeyguardManager.class).isKeyguardLocked()||!getSystemService(PowerManager.class).isInteractive();if(locked)unlockWindow=false;else if(wasLocked)unlockWindow=true;wasLocked=locked;
 WallpaperAccessibilityService a=WallpaperAccessibilityService.instance;
 boolean x=xs()&&now>=xsDue, im=img()&&now>=imageDue;
 if(!paused&&!writing&&(a==null||a.target==null)&&(x||im)){
 boolean allowed=!locked && ("Immediate".equals(policy)||("Home only".equals(policy)&&a!=null&&a.homeVisible())||("Idle".equals(policy)&&a!=null&&now-a.lastActivity>=idle)||("On unlock".equals(policy)&&unlockWindow));
 if(!allowed)status="Deferred";else if(im&&(!x||preferImage)){imageDue=now+imageInterval;preferImage=false;applyImage();}else if(x){if(advance(a)){xsDue=now+interval;preferImage=true;}}
 if(!((xs()&&now>=xsDue)||(img()&&now>=imageDue)))unlockWindow=false;
 }
 getSystemService(NotificationManager.class).notify(ID,notification());handler.postDelayed(tick,1000);}
 boolean advance(WallpaperAccessibilityService a){if(queue.isEmpty()){Intent q=new Intent("android.service.wallpaper.WallpaperService").setPackage(PKG);for(ResolveInfo r:getPackageManager().queryIntentServices(q,0))if(r.serviceInfo.exported&&r.serviceInfo.enabled)queue.add(r.serviceInfo.name);Collections.shuffle(queue);if(queue.size()>1&&queue.get(0).equals(current))Collections.swap(queue,0,1);}if(queue.isEmpty()){status="No XS modules";return true;}String next=queue.get(0);if(automatic&&(a==null||!a.begin(next,xpath))){status="Waiting for accessibility";return false;}current=queue.remove(0);count++;status=current.substring(current.lastIndexOf('$')+1);save();return true;}
 void applyImage(){if(images.isEmpty()){File[] files=new File(folder).listFiles(f->f.isFile()&&f.getName().toLowerCase(Locale.ROOT).matches(".*\\.(jpg|jpeg|png|webp|bmp|gif)"));if(files!=null)for(File f:files)images.add(f.getAbsolutePath());Collections.sort(images);if(shuffle)Collections.shuffle(images);if(images.size()>1&&images.get(0).equals(lastImage))Collections.swap(images,0,1);}if(images.isEmpty()){status="No readable images";return;}final String path=images.remove(0);writing=true;status="Applying image";new Thread(()->{String result;boolean ok=false;try(InputStream in=new FileInputStream(path)){WallpaperManager.getInstance(this).setStream(in,null,true,WallpaperManager.FLAG_SYSTEM);result=new File(path).getName();ok=true;}catch(Exception e){result="Image failed: "+e.getClass().getSimpleName();}final String msg=result;final boolean success=ok;handler.post(()->{writing=false;status=msg;if(success){lastImage=path;imageCount++;save();}});}).start();}
 public int onStartCommand(Intent i,int flags,int startId){String a=i==null?"RESTORE":i.getAction();if("STOP".equals(a)){if(WallpaperAccessibilityService.instance!=null)WallpaperAccessibilityService.instance.cancel();handler.removeCallbacks(tick);stopForeground(true);stopSelf();return START_NOT_STICKY;}long now=SystemClock.elapsedRealtime();if("START".equals(a)){interval=i.getIntExtra("interval",60000);imageInterval=i.getIntExtra("image_interval",300000);idle=i.getIntExtra("idle_seconds",60)*1000L;mode=i.getStringExtra("mode");policy=i.getStringExtra("policy");folder=i.getStringExtra("folder");shuffle=i.getBooleanExtra("shuffle",true);automatic=i.getBooleanExtra("automatic",false);xpath=i.getStringExtra("xpath");if(xpath==null||xpath.isEmpty())xpath=WallpaperAccessibilityService.PRIMARY;images.clear();paused=false;xsDue=imageDue=now;unlockWindow=false;}if("PAUSE".equals(a)){paused=!paused;if(paused&&WallpaperAccessibilityService.instance!=null)WallpaperAccessibilityService.instance.cancel();}if("NEXT".equals(a)){if(img()&&(!xs()||preferImage))imageDue=now;else xsDue=now;}save();startForeground(ID,notification());step();return START_STICKY;}
 public void onDestroy(){handler.removeCallbacks(tick);super.onDestroy();}
}
