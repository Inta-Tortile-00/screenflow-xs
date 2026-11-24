package org.example.screenflow;
import android.view.accessibility.AccessibilityNodeInfo;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.xpath.*;
import javax.xml.namespace.NamespaceContext;
import javax.xml.XMLConstants;
import org.w3c.dom.*;
import java.util.*;

final class XPathEngine {
    static final String NS="http://schemas.android.com/apk/res/android/layout";
    static boolean click(AccessibilityNodeInfo root,String expression) throws Exception {
        Document d=DocumentBuilderFactory.newInstance().newDocumentBuilder().newDocument();
        ArrayList<AccessibilityNodeInfo> nodes=new ArrayList<>();
        try {
            append(d,d,AccessibilityNodeInfo.obtain(root),nodes,0);
            XPath xp=XPathFactory.newInstance().newXPath();
            xp.setNamespaceContext(new NamespaceContext(){public String getNamespaceURI(String p){return "android".equals(p)?NS:XMLConstants.NULL_NS_URI;} public String getPrefix(String u){return NS.equals(u)?"android":null;} public Iterator<String> getPrefixes(String u){return (NS.equals(u)?Collections.singletonList("android"):Collections.<String>emptyList()).iterator();}});
            NodeList matches=(NodeList)xp.evaluate(expression,d,XPathConstants.NODESET);
            if(matches.getLength()!=1 || !(matches.item(0) instanceof Element))return false;
            Element el=(Element)matches.item(0); if(!el.hasAttribute("index"))return false;
            AccessibilityNodeInfo n=nodes.get(Integer.parseInt(el.getAttribute("index")));
            for(int i=0;i<4 && n!=null;i++){
                boolean owned=i>0; AccessibilityNodeInfo next=null;
                try {if(n.isEnabled() && n.isVisibleToUser() && n.isClickable())return n.performAction(AccessibilityNodeInfo.ACTION_CLICK);next=n.getParent();}finally{if(owned)n.recycle();}
                n=next;
            }
            if(n!=null)n.recycle();return false;
        }finally{for(AccessibilityNodeInfo n:nodes)n.recycle();}
    }
    static void append(Document d,Node parent,AccessibilityNodeInfo n,ArrayList<AccessibilityNodeInfo> nodes,int depth){
        if(depth>60 || nodes.size()>=3000){n.recycle();return;}
        String cls=String.valueOf(n.getClassName());if(!cls.matches("[A-Za-z_][A-Za-z0-9_.-]*"))cls="node";
        Element e=d.createElement(cls);e.setAttribute("index",String.valueOf(nodes.size()));nodes.add(n);parent.appendChild(e);
        String id=n.getViewIdResourceName();attr(e,"id",id==null?"":"@"+id);attr(e,"text",n.getText());attr(e,"contentDescription",n.getContentDescription());attr(e,"clickable",n.isClickable());attr(e,"enabled",n.isEnabled());attr(e,"checked",n.isChecked());
        for(int i=0;i<n.getChildCount();i++){AccessibilityNodeInfo child=n.getChild(i);if(child!=null)append(d,e,child,nodes,depth+1);}
    }
    static void attr(Element e,String key,Object v){e.setAttributeNS(NS,"android:"+key,v==null?"":v.toString());}
}
