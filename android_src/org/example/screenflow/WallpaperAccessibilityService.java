package org.example.screenflow;

import android.accessibilityservice.AccessibilityService;
import android.content.*;
import android.app.*;
import android.os.*;
import android.view.accessibility.*;
import android.util.Log;

public class WallpaperAccessibilityService extends AccessibilityService {
    static final String PICKER="com.android.wallpaper.livepicker";
    static final String PRIMARY="//android.widget.Button[@android:id='@com.android.wallpaper.livepicker:id/set_wallpaper']";
    static WallpaperAccessibilityService instance;
    final Handler handler=new Handler(Looper.getMainLooper());
    String target, primary;
    long lastActivity=SystemClock.elapsedRealtime();
    long deadline, nextCheck; int stage;
    final Runnable poll=()->check();
    @Override public void onServiceConnected(){instance=this;}
    @Override public void onAccessibilityEvent(AccessibilityEvent e){if(e.getEventType()!=AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED) lastActivity=SystemClock.elapsedRealtime(); if(target!=null && SystemClock.elapsedRealtime()>=nextCheck) check();}
    @Override public void onInterrupt(){cancel();}
    @Override public void onDestroy(){cancel();instance=null;super.onDestroy();}
    boolean homeVisible(){
        AccessibilityNodeInfo root=getRootInActiveWindow(); if(root==null)return false;
        try { android.content.pm.ResolveInfo r=getPackageManager().resolveActivity(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME), android.content.pm.PackageManager.MATCH_DEFAULT_ONLY); return r!=null && r.activityInfo.packageName.contentEquals(root.getPackageName()); } finally {root.recycle();}
    }
    void cancel(){target=null;handler.removeCallbacks(poll);}
    boolean begin(String klass,String xpath){
        if(getSystemService(KeyguardManager.class).isKeyguardLocked() || !getSystemService(PowerManager.class).isInteractive()) return false;
        if(target!=null)return false;
        cancel(); target=klass;primary=xpath;stage=0;deadline=SystemClock.elapsedRealtime()+20000;
        try {startActivity(new Intent(WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER).setPackage(PICKER).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK).putExtra(WallpaperManager.EXTRA_LIVE_WALLPAPER_COMPONENT,new ComponentName(RotationService.PKG,klass)));}
        catch(Exception e){cancel();Log.w("ScreenFlow","Picker launch failed",e);return false;}
        nextCheck=SystemClock.elapsedRealtime()+750;handler.postDelayed(poll,750);return true;
    }
    void check(){
        handler.removeCallbacks(poll);if(target==null)return;
        if(SystemClock.elapsedRealtime()>deadline || getSystemService(KeyguardManager.class).isKeyguardLocked() || !getSystemService(PowerManager.class).isInteractive()){cancel();return;}
        try {
            WallpaperInfo info=WallpaperManager.getInstance(this).getWallpaperInfo();
            if(stage>0 && info!=null && RotationService.PKG.equals(info.getPackageName()) && target.equals(info.getServiceName())){Log.i("ScreenFlow","Wallpaper verified: "+target);cancel();return;}
            AccessibilityNodeInfo root=getRootInActiveWindow();
            if(root!=null){try{
                if(PICKER.contentEquals(root.getPackageName()) && stage==0){
                    String expr=primary;
                    if(!expr.isEmpty() && XPathEngine.click(root,expr)){stage++;Log.i("ScreenFlow","XPath click stage "+stage);}
                }
            }finally{root.recycle();}}
        }catch(Exception e){Log.w("ScreenFlow","XPath interaction failed",e);cancel();return;}
        nextCheck=SystemClock.elapsedRealtime()+750;handler.postDelayed(poll,750);
    }
}
