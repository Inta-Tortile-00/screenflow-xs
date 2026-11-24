package org.example.screenflow;
import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.util.Log;
import android.widget.Toast;
import java.util.*;

public final class ModuleActions {
 static final String PKG="org.jwz.android.xscreensaver";
 private ModuleActions() {}
 public static Intent settingsIntent(Context c) {
  try {
   WallpaperInfo info=WallpaperManager.getInstance(c).getWallpaperInfo();
   if(info!=null && PKG.equals(info.getPackageName())) {
    String name=info.getSettingsActivity();
    if(name!=null && !name.isEmpty()) {
     if(name.startsWith(".")) name=PKG+name;
     Intent i=new Intent().setClassName(PKG,name).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
     ActivityInfo a=c.getPackageManager().getActivityInfo(i.getComponent(),0);
     if(a.exported && a.enabled) return i;
    }
   }
  } catch(Exception e){Log.w("ScreenFlow","Wallpaper settings unavailable",e);}
  return new Intent().setClassName(c.getPackageName(),"org.kivy.android.PythonActivity").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
 }
 public static String openScreensaver(Context c,String module) {
  if(module==null || module.isEmpty()) return "No upcoming module: start XS background rotation first";
  String label=module.substring(module.lastIndexOf('$')+1);
  ComponentName dream=new ComponentName(PKG,"org.jwz.xscreensaver.gen.Daydream$"+label);
  android.content.ContentResolver resolver=c.getContentResolver();
  String key="screensaver_components", previous=null;
  boolean changed=false;
  try {
   ServiceInfo service=c.getPackageManager().getServiceInfo(dream,0);
   if(!service.enabled || !"android.permission.BIND_DREAM_SERVICE".equals(service.permission)) return "No matching DreamService: "+label;
   if(c.checkSelfPermission("android.permission.WRITE_SECURE_SETTINGS")!=PackageManager.PERMISSION_GRANTED) return "Grant WRITE_SECURE_SETTINGS through ADB first";
   Intent launch=new Intent(Intent.ACTION_MAIN).setClassName("com.android.systemui","com.android.systemui.Somnambulator").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
   previous=android.provider.Settings.Secure.getString(resolver,key);
   if(!android.provider.Settings.Secure.putString(resolver,key,dream.flattenToString())) return "Screensaver selection rejected";
   changed=true;
   c.startActivity(launch);
   Log.i("ScreenFlow","Dream launch requested: "+dream.flattenToString());
   return "Standalone screensaver requested: "+label;
  }catch(Exception e){
   if(changed) try {android.provider.Settings.Secure.putString(resolver,key,previous);}catch(Exception rollback){Log.w("ScreenFlow","Dream selection rollback failed",rollback);}
   Log.w("ScreenFlow","Dream launch failed",e);
   return "Screensaver launch failed: "+e.getClass().getSimpleName();
  }
 }
}
