import{_ as Vt,o as St,H as Nt,b as h,c as $,f as l,w as i,h as Ht,p as Lt,E as O,g as _,r as k,I as Mt,q as Yt,B as Et,v as zt,F as Y,m as E,z as _t,e as n,i as f,t as w}from"./index-BBD6CpIy.js";const Rt={class:"agent-report-page"},Bt={class:"header-row"},Dt={class:"header-actions"},Pt={key:0,class:"report-content"},Wt={class:"kpi-value"},Ut={class:"kpi-value"},qt={class:"kpi-value"},Ft={class:"kpi-value"},It={class:"brief"},Tt={class:"analysis-list"},jt={class:"analysis-list"},Qt={class:"decision-item"},Jt={class:"decision-item"},Gt={__name:"Report",setup(Kt){const z=k(!1),S=k([]),u=k(null),P=Mt(),W=k(!1),s=k({building_id:"",building_ids:[],start_time:"2021-01-01 00:00:00",end_time:"2021-12-31 23:59:59",top_n:8,carbon_factor:.785}),U=k(null),q=k(null),F=k(null),I=k(null),x={monthly:null,comparison:null,anomaly:null,cop:null},b=(a,t=2)=>{const e=Number(a);return Number.isNaN(e)?"0.00":e.toFixed(t)},N=a=>{a==="q1"?(s.value.start_time="2021-01-01 00:00:00",s.value.end_time="2021-03-31 23:59:59"):a==="q2"?(s.value.start_time="2021-04-01 00:00:00",s.value.end_time="2021-06-30 23:59:59"):a==="summer"?(s.value.start_time="2021-06-01 00:00:00",s.value.end_time="2021-08-31 23:59:59"):(s.value.start_time="2021-01-01 00:00:00",s.value.end_time="2021-12-31 23:59:59")},ft=a=>{const t=String(a||"").trim().toLowerCase();return t==="1"||t==="true"||t==="yes"},yt=()=>{const a=P.query||{};if(typeof a.building_id=="string"&&(s.value.building_id=a.building_id.trim()),typeof a.building_ids=="string"&&(s.value.building_ids=a.building_ids.split(",").map(t=>t.trim()).filter(t=>t)),typeof a.start_time=="string"&&(s.value.start_time=a.start_time.trim()),typeof a.end_time=="string"&&(s.value.end_time=a.end_time.trim()),typeof a.top_n=="string"){const t=Number(a.top_n);!Number.isNaN(t)&&t>=1&&t<=20&&(s.value.top_n=t)}if(typeof a.carbon_factor=="string"){const t=Number(a.carbon_factor);!Number.isNaN(t)&&t>=0&&t<=2&&(s.value.carbon_factor=t)}},bt=async()=>{var a;try{const t=await Lt.getBuildings();S.value=((a=t.data)==null?void 0:a.buildings)||[]}catch{S.value=[]}},H=(a,t)=>t!=null&&t.value?(x[a]&&x[a].dispose(),x[a]=zt(t.value),x[a]):null,ht=()=>{var p,r;const a=H("monthly",U);if(!a)return;const t=((r=(p=u.value)==null?void 0:p.charts)==null?void 0:r.monthly_energy)||[],e=t.map(d=>d.month);a.setOption({tooltip:{trigger:"axis"},legend:{top:0},grid:{left:40,right:20,top:40,bottom:30},xAxis:{type:"category",data:e},yAxis:{type:"value",name:"kWh/m3"},series:[{name:"电耗(kWh)",type:"line",smooth:!0,data:t.map(d=>d.electricity_kwh)},{name:"HVAC(kWh)",type:"line",smooth:!0,data:t.map(d=>d.hvac_kwh)},{name:"水耗(m3)",type:"bar",yAxisIndex:0,data:t.map(d=>d.water_m3)}]})},xt=()=>{var e,p;const a=H("comparison",q);if(!a)return;const t=((p=(e=u.value)==null?void 0:e.charts)==null?void 0:p.building_comparison)||[];a.setOption({tooltip:{trigger:"axis"},grid:{left:40,right:20,top:20,bottom:70},xAxis:{type:"category",axisLabel:{interval:0,rotate:30},data:t.map(r=>r.building_id)},yAxis:{type:"value",name:"kWh"},series:[{name:"总电耗",type:"bar",data:t.map(r=>r.total_electricity_kwh),itemStyle:{color:"#2d7ff9"}}]})},kt=()=>{var p,r,d,c,y,C;const a=H("anomaly",F);if(!a)return;const t=((d=(r=(p=u.value)==null?void 0:p.charts)==null?void 0:r.anomaly_distribution)==null?void 0:d.by_metric)||[],e=((C=(y=(c=u.value)==null?void 0:c.charts)==null?void 0:y.anomaly_distribution)==null?void 0:C.by_severity)||[];a.setOption({tooltip:{trigger:"item"},legend:{top:0},series:[{name:"按指标",type:"pie",radius:["35%","55%"],center:["30%","60%"],data:t},{name:"按等级",type:"pie",radius:["35%","55%"],center:["75%","60%"],data:e}]})},wt=()=>{var e,p;const a=H("cop",I);if(!a)return;const t=((p=(e=u.value)==null?void 0:e.charts)==null?void 0:p.cop_trend)||[];a.setOption({tooltip:{trigger:"axis"},grid:{left:40,right:20,top:20,bottom:30},xAxis:{type:"category",data:t.map(r=>r.month)},yAxis:{type:"value",name:"COP"},series:[{name:"月均COP",type:"line",smooth:!0,areaStyle:{},data:t.map(r=>r.avg_cop)}]})},Ct=()=>{ht(),xt(),kt(),wt()},T=async(a={})=>{var e,p;const{silentSuccess:t=!1}=a;z.value=!0;try{const r={building_id:s.value.building_id||null,building_ids:s.value.building_ids.length?s.value.building_ids:null,start_time:s.value.start_time||null,end_time:s.value.end_time||null,top_n:s.value.top_n,carbon_factor:s.value.carbon_factor},d=await Yt.getAgentReport(r);u.value=d.data,await Et(),Ct(),t||O.success("报表生成成功")}catch(r){console.error(r),O.error(((p=(e=r==null?void 0:r.response)==null?void 0:e.data)==null?void 0:p.detail)||"报表生成失败")}finally{z.value=!1}},v=a=>String(a??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;"),L=a=>JSON.stringify(a).replace(/</g,"\\u003c"),$t=()=>{const a=new Date,t=e=>String(e).padStart(2,"0");return`${a.getFullYear()}${t(a.getMonth()+1)}${t(a.getDate())}_${t(a.getHours())}${t(a.getMinutes())}${t(a.getSeconds())}`},j=(a={})=>{var G,K,X,Z,tt,et,at,it,lt,st,nt,ot,rt,dt,ut,ct,pt,mt,vt,gt;const{silentSuccess:t=!1}=a;if(!u.value){O.warning("请先生成报表再导出");return}const e=u.value,p=((G=e==null?void 0:e.report_meta)==null?void 0:G.time_range)||{},r=((K=e==null?void 0:e.charts)==null?void 0:K.monthly_energy)||[],d=((X=e==null?void 0:e.charts)==null?void 0:X.building_comparison)||[],c=((tt=(Z=e==null?void 0:e.charts)==null?void 0:Z.anomaly_distribution)==null?void 0:tt.by_metric)||[],y=((at=(et=e==null?void 0:e.charts)==null?void 0:et.anomaly_distribution)==null?void 0:at.by_severity)||[],C=((it=e==null?void 0:e.charts)==null?void 0:it.cop_trend)||[],M={tooltip:{trigger:"axis"},legend:{top:0},grid:{left:40,right:20,top:40,bottom:30},xAxis:{type:"category",data:r.map(m=>m.month)},yAxis:{type:"value",name:"kWh/m3"},series:[{name:"电耗(kWh)",type:"line",smooth:!0,data:r.map(m=>m.electricity_kwh)},{name:"HVAC(kWh)",type:"line",smooth:!0,data:r.map(m=>m.hvac_kwh)},{name:"水耗(m3)",type:"bar",data:r.map(m=>m.water_m3)}]},R={tooltip:{trigger:"axis"},grid:{left:40,right:20,top:20,bottom:70},xAxis:{type:"category",axisLabel:{interval:0,rotate:30},data:d.map(m=>m.building_id)},yAxis:{type:"value",name:"kWh"},series:[{name:"总电耗",type:"bar",data:d.map(m=>m.total_electricity_kwh),itemStyle:{color:"#2d7ff9"}}]},B={tooltip:{trigger:"item"},legend:{top:0},series:[{name:"按指标",type:"pie",radius:["35%","55%"],center:["30%","60%"],data:c},{name:"按等级",type:"pie",radius:["35%","55%"],center:["75%","60%"],data:y}]},g={tooltip:{trigger:"axis"},grid:{left:40,right:20,top:20,bottom:30},xAxis:{type:"category",data:C.map(m=>m.month)},yAxis:{type:"value",name:"COP"},series:[{name:"月均COP",type:"line",smooth:!0,areaStyle:{},data:C.map(m=>m.avg_cop)}]},D=new Date().toLocaleString("zh-CN"),o=`智能体统计报表_${$t()}`,A=`<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${v(o)}</title>
  <style>
    body { margin: 0; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; background: #f3f5f8; color: #0f172a; }
    .wrap { max-width: 1240px; margin: 20px auto; padding: 0 16px; }
    .panel { background: #fff; border-radius: 12px; box-shadow: 0 10px 25px rgba(2, 20, 43, 0.08); margin-bottom: 16px; overflow: hidden; }
    .panel-header { padding: 16px 20px; border-bottom: 1px solid #e5e7eb; }
    .panel-body { padding: 16px 20px; }
    h1 { margin: 0; font-size: 24px; }
    .meta { margin-top: 6px; color: #475569; font-size: 14px; }
    .meta-line { margin-top: 4px; color: #64748b; font-size: 13px; }
    .kpis { display: grid; grid-template-columns: repeat(4, minmax(180px, 1fr)); gap: 12px; }
    .kpi { background: #f8fafc; border-radius: 10px; padding: 12px; border: 1px solid #e2e8f0; }
    .kpi-label { color: #64748b; font-size: 13px; }
    .kpi-value { margin-top: 8px; font-size: 28px; font-weight: 700; color: #0b1220; }
    .kpi-unit { margin-top: 4px; color: #64748b; font-size: 12px; }
    .grid-2 { display: grid; grid-template-columns: repeat(2, minmax(320px, 1fr)); gap: 12px; }
    .chart-card { border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; background: #fff; }
    .chart-title { padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #334155; }
    .chart { height: 320px; }
    .analysis-grid { display: grid; grid-template-columns: repeat(2, minmax(320px, 1fr)); gap: 12px; }
    .list { margin: 0; padding-left: 20px; color: #1f2937; line-height: 1.8; }
    .brief { margin: 0 0 10px 0; color: #475569; }
    .row { display: flex; justify-content: space-between; margin: 6px 0; color: #334155; }
    @media (max-width: 900px) {
      .kpis, .grid-2, .analysis-grid { grid-template-columns: 1fr; }
      .chart { height: 280px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <div class="panel-header">
        <h1>建筑能源智能体统计报表</h1>
        <div class="meta">导出时间：${v(D)}</div>
        <div class="meta-line">统计范围：${v(p.start_time||"未设置")} ~ ${v(p.end_time||"未设置")}</div>
        <div class="meta-line">聚焦建筑：${v(((lt=e==null?void 0:e.report_meta)==null?void 0:lt.focus_building)||"全部")}</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">关键指标</div>
      <div class="panel-body">
        <div class="kpis">
          <div class="kpi"><div class="kpi-label">总电耗</div><div class="kpi-value">${v(b((st=e==null?void 0:e.kpis)==null?void 0:st.total_electricity_kwh))}</div><div class="kpi-unit">kWh</div></div>
          <div class="kpi"><div class="kpi-label">平均COP</div><div class="kpi-value">${v(b((nt=e==null?void 0:e.kpis)==null?void 0:nt.average_cop,3))}</div><div class="kpi-unit">效率指数</div></div>
          <div class="kpi"><div class="kpi-label">异常点数</div><div class="kpi-value">${v(String(((ot=e==null?void 0:e.kpis)==null?void 0:ot.anomaly_count)??0))}</div><div class="kpi-unit">个</div></div>
          <div class="kpi"><div class="kpi-label">碳排放估算</div><div class="kpi-value">${v(b((rt=e==null?void 0:e.kpis)==null?void 0:rt.carbon_emission_ton,3))}</div><div class="kpi-unit">吨CO2</div></div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">图表分析</div>
      <div class="panel-body">
        <div class="grid-2">
          <div class="chart-card"><div class="chart-title">月度能耗统计</div><div id="chart-monthly" class="chart"></div></div>
          <div class="chart-card"><div class="chart-title">分建筑能耗对比</div><div id="chart-comparison" class="chart"></div></div>
          <div class="chart-card"><div class="chart-title">异常分布</div><div id="chart-anomaly" class="chart"></div></div>
          <div class="chart-card"><div class="chart-title">COP效率趋势</div><div id="chart-cop" class="chart"></div></div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">分析结论与建议</div>
      <div class="panel-body">
        <div class="analysis-grid">
          <div>
            <p class="brief">${v(((dt=e==null?void 0:e.analysis)==null?void 0:dt.brief)||"")}</p>
            <ul class="list">
              ${(((ut=e==null?void 0:e.analysis)==null?void 0:ut.conclusions)||[]).map(m=>`<li>${v(m)}</li>`).join("")}
            </ul>
          </div>
          <div>
            <ul class="list">
              ${(((ct=e==null?void 0:e.analysis)==null?void 0:ct.recommendations)||[]).map(m=>`<li>${v(m)}</li>`).join("")}
            </ul>
            <div class="row"><span>潜在节能量</span><strong>${v(b((mt=(pt=e==null?void 0:e.decision_support)==null?void 0:pt.energy_saving)==null?void 0:mt.potential_savings_kwh))} kWh</strong></div>
            <div class="row"><span>潜在节能率</span><strong>${v(b((gt=(vt=e==null?void 0:e.decision_support)==null?void 0:vt.energy_saving)==null?void 0:gt.potential_savings_pct,2))}%</strong></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"><\/script>
  <script>
    const options = {
      monthly: ${L(M)},
      comparison: ${L(R)},
      anomaly: ${L(B)},
      cop: ${L(g)}
    };

    const charts = [
      echarts.init(document.getElementById('chart-monthly')),
      echarts.init(document.getElementById('chart-comparison')),
      echarts.init(document.getElementById('chart-anomaly')),
      echarts.init(document.getElementById('chart-cop'))
    ];

    charts[0].setOption(options.monthly);
    charts[1].setOption(options.comparison);
    charts[2].setOption(options.anomaly);
    charts[3].setOption(options.cop);

    window.addEventListener('resize', () => charts.forEach(c => c.resize()));
  <\/script>
</body>
</html>`,At=new Blob([A],{type:"text/html;charset=utf-8;"}),J=URL.createObjectURL(At),V=document.createElement("a");V.href=J,V.download=`${o}.html`,document.body.appendChild(V),V.click(),document.body.removeChild(V),URL.revokeObjectURL(J),t||O.success("HTML报表导出成功")},Ot=async()=>{if(W.value)return;const a=P.query||{},t=ft(a.auto_report),e=String(a.auto_export||"").toLowerCase()==="html";if(!(!t&&!e)){if(W.value=!0,await T({silentSuccess:!0}),e&&u.value){j({silentSuccess:!0}),O.success("已按智能助手指令自动生成并导出HTML报表");return}u.value&&O.success("已按智能助手指令自动生成可视化报表")}},Q=()=>{Object.values(x).forEach(a=>{a&&a.resize()})};return St(async()=>{await bt(),yt(),window.addEventListener("resize",Q),await Ot()}),Nt(()=>{window.removeEventListener("resize",Q),Object.keys(x).forEach(a=>{x[a]&&(x[a].dispose(),x[a]=null)})}),(a,t)=>{const e=_("el-button"),p=_("el-option"),r=_("el-select"),d=_("el-form-item"),c=_("el-col"),y=_("el-row"),C=_("el-date-picker"),M=_("el-input-number"),R=_("el-button-group"),B=_("el-form"),g=_("el-card"),D=_("el-divider");return h(),$("div",Rt,[l(g,{class:"control-card",shadow:"never"},{header:i(()=>[n("div",Bt,[t[12]||(t[12]=n("div",null,[n("h2",null,"智能体统计报表工作台"),n("p",null,"一键生成基础统计、分析诊断与决策支持报表")],-1)),n("div",Dt,[l(e,{type:"primary",loading:z.value,onClick:T},{default:i(()=>[...t[10]||(t[10]=[f("生成可视化报表",-1)])]),_:1},8,["loading"]),l(e,{type:"success",disabled:!u.value,onClick:j},{default:i(()=>[...t[11]||(t[11]=[f("导出HTML报表",-1)])]),_:1},8,["disabled"])])])]),default:i(()=>[l(B,{model:s.value,"label-width":"120px"},{default:i(()=>[l(y,{gutter:16},{default:i(()=>[l(c,{xs:24,md:12},{default:i(()=>[l(d,{label:"聚焦建筑"},{default:i(()=>[l(r,{modelValue:s.value.building_id,"onUpdate:modelValue":t[0]||(t[0]=o=>s.value.building_id=o),placeholder:"可选，默认全部",clearable:"",filterable:""},{default:i(()=>[(h(!0),$(Y,null,E(S.value,o=>(h(),_t(p,{key:o.building_id,label:o.building_id,value:o.building_id},null,8,["label","value"]))),128))]),_:1},8,["modelValue"])]),_:1})]),_:1}),l(c,{xs:24,md:12},{default:i(()=>[l(d,{label:"对比建筑"},{default:i(()=>[l(r,{modelValue:s.value.building_ids,"onUpdate:modelValue":t[1]||(t[1]=o=>s.value.building_ids=o),multiple:"",clearable:"",filterable:"",placeholder:"可多选，不选则自动取全部"},{default:i(()=>[(h(!0),$(Y,null,E(S.value,o=>(h(),_t(p,{key:o.building_id,label:o.building_id,value:o.building_id},null,8,["label","value"]))),128))]),_:1},8,["modelValue"])]),_:1})]),_:1})]),_:1}),l(y,{gutter:16},{default:i(()=>[l(c,{xs:24,md:12},{default:i(()=>[l(d,{label:"开始时间"},{default:i(()=>[l(C,{modelValue:s.value.start_time,"onUpdate:modelValue":t[2]||(t[2]=o=>s.value.start_time=o),type:"datetime","value-format":"YYYY-MM-DD HH:mm:ss",format:"YYYY-MM-DD HH:mm:ss",placeholder:"选择开始时间"},null,8,["modelValue"])]),_:1})]),_:1}),l(c,{xs:24,md:12},{default:i(()=>[l(d,{label:"结束时间"},{default:i(()=>[l(C,{modelValue:s.value.end_time,"onUpdate:modelValue":t[3]||(t[3]=o=>s.value.end_time=o),type:"datetime","value-format":"YYYY-MM-DD HH:mm:ss",format:"YYYY-MM-DD HH:mm:ss",placeholder:"选择结束时间"},null,8,["modelValue"])]),_:1})]),_:1})]),_:1}),l(y,{gutter:16},{default:i(()=>[l(c,{xs:24,md:12},{default:i(()=>[l(d,{label:"对比建筑上限"},{default:i(()=>[l(M,{modelValue:s.value.top_n,"onUpdate:modelValue":t[4]||(t[4]=o=>s.value.top_n=o),min:1,max:20},null,8,["modelValue"])]),_:1})]),_:1}),l(c,{xs:24,md:12},{default:i(()=>[l(d,{label:"碳排放因子"},{default:i(()=>[l(M,{modelValue:s.value.carbon_factor,"onUpdate:modelValue":t[5]||(t[5]=o=>s.value.carbon_factor=o),precision:3,step:.01,min:0,max:2},null,8,["modelValue"]),t[13]||(t[13]=n("span",{class:"unit-tip"},"kgCO2/kWh",-1))]),_:1})]),_:1})]),_:1}),l(d,{label:"快速区间"},{default:i(()=>[l(R,null,{default:i(()=>[l(e,{onClick:t[6]||(t[6]=o=>N("q1"))},{default:i(()=>[...t[14]||(t[14]=[f("2021 Q1",-1)])]),_:1}),l(e,{onClick:t[7]||(t[7]=o=>N("q2"))},{default:i(()=>[...t[15]||(t[15]=[f("2021 Q2",-1)])]),_:1}),l(e,{onClick:t[8]||(t[8]=o=>N("summer"))},{default:i(()=>[...t[16]||(t[16]=[f("2021 夏季",-1)])]),_:1}),l(e,{onClick:t[9]||(t[9]=o=>N("year"))},{default:i(()=>[...t[17]||(t[17]=[f("2021 全年",-1)])]),_:1})]),_:1})]),_:1})]),_:1},8,["model"])]),_:1}),u.value?(h(),$("div",Pt,[l(y,{gutter:16,class:"kpi-grid"},{default:i(()=>[l(c,{xs:12,md:6},{default:i(()=>[l(g,{class:"kpi-card",shadow:"hover"},{default:i(()=>[t[18]||(t[18]=n("div",{class:"kpi-label"},"总电耗",-1)),n("div",Wt,w(b(u.value.kpis.total_electricity_kwh)),1),t[19]||(t[19]=n("div",{class:"kpi-unit"},"kWh",-1))]),_:1})]),_:1}),l(c,{xs:12,md:6},{default:i(()=>[l(g,{class:"kpi-card",shadow:"hover"},{default:i(()=>[t[20]||(t[20]=n("div",{class:"kpi-label"},"平均COP",-1)),n("div",Ut,w(b(u.value.kpis.average_cop,3)),1),t[21]||(t[21]=n("div",{class:"kpi-unit"},"效率指数",-1))]),_:1})]),_:1}),l(c,{xs:12,md:6},{default:i(()=>[l(g,{class:"kpi-card",shadow:"hover"},{default:i(()=>[t[22]||(t[22]=n("div",{class:"kpi-label"},"异常点数",-1)),n("div",qt,w(u.value.kpis.anomaly_count),1),t[23]||(t[23]=n("div",{class:"kpi-unit"},"个",-1))]),_:1})]),_:1}),l(c,{xs:12,md:6},{default:i(()=>[l(g,{class:"kpi-card",shadow:"hover"},{default:i(()=>[t[24]||(t[24]=n("div",{class:"kpi-label"},"碳排放估算",-1)),n("div",Ft,w(b(u.value.kpis.carbon_emission_ton,3)),1),t[25]||(t[25]=n("div",{class:"kpi-unit"},"吨CO2",-1))]),_:1})]),_:1})]),_:1}),l(y,{gutter:16,class:"chart-grid"},{default:i(()=>[l(c,{xs:24,lg:12},{default:i(()=>[l(g,{shadow:"never"},{header:i(()=>[...t[26]||(t[26]=[f("月度能耗统计",-1)])]),default:i(()=>[n("div",{ref_key:"monthlyChartRef",ref:U,class:"chart-box"},null,512)]),_:1})]),_:1}),l(c,{xs:24,lg:12},{default:i(()=>[l(g,{shadow:"never"},{header:i(()=>[...t[27]||(t[27]=[f("分建筑能耗对比",-1)])]),default:i(()=>[n("div",{ref_key:"comparisonChartRef",ref:q,class:"chart-box"},null,512)]),_:1})]),_:1}),l(c,{xs:24,lg:12},{default:i(()=>[l(g,{shadow:"never"},{header:i(()=>[...t[28]||(t[28]=[f("异常分布",-1)])]),default:i(()=>[n("div",{ref_key:"anomalyChartRef",ref:F,class:"chart-box"},null,512)]),_:1})]),_:1}),l(c,{xs:24,lg:12},{default:i(()=>[l(g,{shadow:"never"},{header:i(()=>[...t[29]||(t[29]=[f("COP效率趋势",-1)])]),default:i(()=>[n("div",{ref_key:"copChartRef",ref:I,class:"chart-box"},null,512)]),_:1})]),_:1})]),_:1}),l(y,{gutter:16,class:"analysis-grid"},{default:i(()=>[l(c,{xs:24,lg:12},{default:i(()=>[l(g,{shadow:"never"},{header:i(()=>[...t[30]||(t[30]=[f("简要分析结论",-1)])]),default:i(()=>[n("p",It,w(u.value.analysis.brief),1),n("ul",Tt,[(h(!0),$(Y,null,E(u.value.analysis.conclusions,(o,A)=>(h(),$("li",{key:`c-${A}`},w(o),1))),128))])]),_:1})]),_:1}),l(c,{xs:24,lg:12},{default:i(()=>[l(g,{shadow:"never"},{header:i(()=>[...t[31]||(t[31]=[f("决策支持建议",-1)])]),default:i(()=>[n("ul",jt,[(h(!0),$(Y,null,E(u.value.analysis.recommendations,(o,A)=>(h(),$("li",{key:`r-${A}`},w(o),1))),128))]),l(D),n("div",Qt,[t[32]||(t[32]=n("span",null,"潜在节能量:",-1)),n("strong",null,w(b(u.value.decision_support.energy_saving.potential_savings_kwh))+" kWh",1)]),n("div",Jt,[t[33]||(t[33]=n("span",null,"潜在节能率:",-1)),n("strong",null,w(b(u.value.decision_support.energy_saving.potential_savings_pct,2))+"%",1)])]),_:1})]),_:1})]),_:1})])):Ht("",!0)])}}},Zt=Vt(Gt,[["__scopeId","data-v-7fff2711"]]);export{Zt as default};
