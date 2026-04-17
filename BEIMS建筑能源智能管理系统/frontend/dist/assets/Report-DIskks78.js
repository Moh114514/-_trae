import{_ as xe,o as ke,H as we,b,c as w,f as i,w as a,h as Ce,p as $e,g as _,r as C,F as L,m as z,z as ue,e as s,i as f,t as k,q as Oe,B as Ve,E,v as Ae}from"./index-BMEOy2oG.js";const Ye={class:"agent-report-page"},Me={class:"header-row"},He={class:"header-actions"},Se={key:0,class:"report-content"},Le={class:"kpi-value"},ze={class:"kpi-value"},Ee={class:"kpi-value"},De={class:"kpi-value"},Re={class:"brief"},Be={class:"analysis-list"},We={class:"analysis-list"},Ne={class:"decision-item"},Pe={class:"decision-item"},Ue={__name:"Report",setup(je){const D=C(!1),A=C([]),p=C(null),o=C({building_id:"",building_ids:[],start_time:"2021-01-01 00:00:00",end_time:"2021-12-31 23:59:59",top_n:8,carbon_factor:.785}),N=C(null),P=C(null),U=C(null),j=C(null),x={monthly:null,comparison:null,anomaly:null,cop:null},h=(t,e=2)=>{const l=Number(t);return Number.isNaN(l)?"0.00":l.toFixed(e)},Y=t=>{t==="q1"?(o.value.start_time="2021-01-01 00:00:00",o.value.end_time="2021-03-31 23:59:59"):t==="q2"?(o.value.start_time="2021-04-01 00:00:00",o.value.end_time="2021-06-30 23:59:59"):t==="summer"?(o.value.start_time="2021-06-01 00:00:00",o.value.end_time="2021-08-31 23:59:59"):(o.value.start_time="2021-01-01 00:00:00",o.value.end_time="2021-12-31 23:59:59")},ce=async()=>{var t;try{const e=await $e.getBuildings();A.value=((t=e.data)==null?void 0:t.buildings)||[]}catch{A.value=[]}},M=(t,e)=>e!=null&&e.value?(x[t]&&x[t].dispose(),x[t]=Ae(e.value),x[t]):null,me=()=>{var u,m;const t=M("monthly",N);if(!t)return;const e=((m=(u=p.value)==null?void 0:u.charts)==null?void 0:m.monthly_energy)||[],l=e.map(r=>r.month);t.setOption({tooltip:{trigger:"axis"},legend:{top:0},grid:{left:40,right:20,top:40,bottom:30},xAxis:{type:"category",data:l},yAxis:{type:"value",name:"kWh/m3"},series:[{name:"电耗(kWh)",type:"line",smooth:!0,data:e.map(r=>r.electricity_kwh)},{name:"HVAC(kWh)",type:"line",smooth:!0,data:e.map(r=>r.hvac_kwh)},{name:"水耗(m3)",type:"bar",yAxisIndex:0,data:e.map(r=>r.water_m3)}]})},ve=()=>{var l,u;const t=M("comparison",P);if(!t)return;const e=((u=(l=p.value)==null?void 0:l.charts)==null?void 0:u.building_comparison)||[];t.setOption({tooltip:{trigger:"axis"},grid:{left:40,right:20,top:20,bottom:70},xAxis:{type:"category",axisLabel:{interval:0,rotate:30},data:e.map(m=>m.building_id)},yAxis:{type:"value",name:"kWh"},series:[{name:"总电耗",type:"bar",data:e.map(m=>m.total_electricity_kwh),itemStyle:{color:"#2d7ff9"}}]})},ge=()=>{var u,m,r,d,y,$;const t=M("anomaly",U);if(!t)return;const e=((r=(m=(u=p.value)==null?void 0:u.charts)==null?void 0:m.anomaly_distribution)==null?void 0:r.by_metric)||[],l=(($=(y=(d=p.value)==null?void 0:d.charts)==null?void 0:y.anomaly_distribution)==null?void 0:$.by_severity)||[];t.setOption({tooltip:{trigger:"item"},legend:{top:0},series:[{name:"按指标",type:"pie",radius:["35%","55%"],center:["30%","60%"],data:e},{name:"按等级",type:"pie",radius:["35%","55%"],center:["75%","60%"],data:l}]})},_e=()=>{var l,u;const t=M("cop",j);if(!t)return;const e=((u=(l=p.value)==null?void 0:l.charts)==null?void 0:u.cop_trend)||[];t.setOption({tooltip:{trigger:"axis"},grid:{left:40,right:20,top:20,bottom:30},xAxis:{type:"category",data:e.map(m=>m.month)},yAxis:{type:"value",name:"COP"},series:[{name:"月均COP",type:"line",smooth:!0,areaStyle:{},data:e.map(m=>m.avg_cop)}]})},fe=()=>{me(),ve(),ge(),_e()},ye=async()=>{var t,e;D.value=!0;try{const l={building_id:o.value.building_id||null,building_ids:o.value.building_ids.length?o.value.building_ids:null,start_time:o.value.start_time||null,end_time:o.value.end_time||null,top_n:o.value.top_n,carbon_factor:o.value.carbon_factor},u=await Oe.getAgentReport(l);p.value=u.data,await Ve(),fe(),E.success("报表生成成功")}catch(l){console.error(l),E.error(((e=(t=l==null?void 0:l.response)==null?void 0:t.data)==null?void 0:e.detail)||"报表生成失败")}finally{D.value=!1}},v=t=>String(t??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;"),H=t=>JSON.stringify(t).replace(/</g,"\\u003c"),he=()=>{const t=new Date,e=l=>String(l).padStart(2,"0");return`${t.getFullYear()}${e(t.getMonth()+1)}${e(t.getDate())}_${e(t.getHours())}${e(t.getMinutes())}${e(t.getSeconds())}`},be=()=>{var T,q,F,Q,J,G,K,X,Z,ee,te,ae,ie,le,se,ne,oe,de,re,pe;if(!p.value){E.warning("请先生成报表再导出");return}const t=p.value,e=((T=t==null?void 0:t.report_meta)==null?void 0:T.time_range)||{},l=((q=t==null?void 0:t.charts)==null?void 0:q.monthly_energy)||[],u=((F=t==null?void 0:t.charts)==null?void 0:F.building_comparison)||[],m=((J=(Q=t==null?void 0:t.charts)==null?void 0:Q.anomaly_distribution)==null?void 0:J.by_metric)||[],r=((K=(G=t==null?void 0:t.charts)==null?void 0:G.anomaly_distribution)==null?void 0:K.by_severity)||[],d=((X=t==null?void 0:t.charts)==null?void 0:X.cop_trend)||[],y={tooltip:{trigger:"axis"},legend:{top:0},grid:{left:40,right:20,top:40,bottom:30},xAxis:{type:"category",data:l.map(c=>c.month)},yAxis:{type:"value",name:"kWh/m3"},series:[{name:"电耗(kWh)",type:"line",smooth:!0,data:l.map(c=>c.electricity_kwh)},{name:"HVAC(kWh)",type:"line",smooth:!0,data:l.map(c=>c.hvac_kwh)},{name:"水耗(m3)",type:"bar",data:l.map(c=>c.water_m3)}]},$={tooltip:{trigger:"axis"},grid:{left:40,right:20,top:20,bottom:70},xAxis:{type:"category",axisLabel:{interval:0,rotate:30},data:u.map(c=>c.building_id)},yAxis:{type:"value",name:"kWh"},series:[{name:"总电耗",type:"bar",data:u.map(c=>c.total_electricity_kwh),itemStyle:{color:"#2d7ff9"}}]},S={tooltip:{trigger:"item"},legend:{top:0},series:[{name:"按指标",type:"pie",radius:["35%","55%"],center:["30%","60%"],data:m},{name:"按等级",type:"pie",radius:["35%","55%"],center:["75%","60%"],data:r}]},R={tooltip:{trigger:"axis"},grid:{left:40,right:20,top:20,bottom:30},xAxis:{type:"category",data:d.map(c=>c.month)},yAxis:{type:"value",name:"COP"},series:[{name:"月均COP",type:"line",smooth:!0,areaStyle:{},data:d.map(c=>c.avg_cop)}]},B=new Date().toLocaleString("zh-CN"),g=`智能体统计报表_${he()}`,W=`<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${v(g)}</title>
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
        <div class="meta">导出时间：${v(B)}</div>
        <div class="meta-line">统计范围：${v(e.start_time||"未设置")} ~ ${v(e.end_time||"未设置")}</div>
        <div class="meta-line">聚焦建筑：${v(((Z=t==null?void 0:t.report_meta)==null?void 0:Z.focus_building)||"全部")}</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">关键指标</div>
      <div class="panel-body">
        <div class="kpis">
          <div class="kpi"><div class="kpi-label">总电耗</div><div class="kpi-value">${v(h((ee=t==null?void 0:t.kpis)==null?void 0:ee.total_electricity_kwh))}</div><div class="kpi-unit">kWh</div></div>
          <div class="kpi"><div class="kpi-label">平均COP</div><div class="kpi-value">${v(h((te=t==null?void 0:t.kpis)==null?void 0:te.average_cop,3))}</div><div class="kpi-unit">效率指数</div></div>
          <div class="kpi"><div class="kpi-label">异常点数</div><div class="kpi-value">${v(String(((ae=t==null?void 0:t.kpis)==null?void 0:ae.anomaly_count)??0))}</div><div class="kpi-unit">个</div></div>
          <div class="kpi"><div class="kpi-label">碳排放估算</div><div class="kpi-value">${v(h((ie=t==null?void 0:t.kpis)==null?void 0:ie.carbon_emission_ton,3))}</div><div class="kpi-unit">吨CO2</div></div>
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
            <p class="brief">${v(((le=t==null?void 0:t.analysis)==null?void 0:le.brief)||"")}</p>
            <ul class="list">
              ${(((se=t==null?void 0:t.analysis)==null?void 0:se.conclusions)||[]).map(c=>`<li>${v(c)}</li>`).join("")}
            </ul>
          </div>
          <div>
            <ul class="list">
              ${(((ne=t==null?void 0:t.analysis)==null?void 0:ne.recommendations)||[]).map(c=>`<li>${v(c)}</li>`).join("")}
            </ul>
            <div class="row"><span>潜在节能量</span><strong>${v(h((de=(oe=t==null?void 0:t.decision_support)==null?void 0:oe.energy_saving)==null?void 0:de.potential_savings_kwh))} kWh</strong></div>
            <div class="row"><span>潜在节能率</span><strong>${v(h((pe=(re=t==null?void 0:t.decision_support)==null?void 0:re.energy_saving)==null?void 0:pe.potential_savings_pct,2))}%</strong></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"><\/script>
  <script>
    const options = {
      monthly: ${H(y)},
      comparison: ${H($)},
      anomaly: ${H(S)},
      cop: ${H(R)}
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
</html>`,n=new Blob([W],{type:"text/html;charset=utf-8;"}),O=URL.createObjectURL(n),V=document.createElement("a");V.href=O,V.download=`${g}.html`,document.body.appendChild(V),V.click(),document.body.removeChild(V),URL.revokeObjectURL(O),E.success("HTML报表导出成功")},I=()=>{Object.values(x).forEach(t=>{t&&t.resize()})};return ke(async()=>{await ce(),window.addEventListener("resize",I)}),we(()=>{window.removeEventListener("resize",I),Object.keys(x).forEach(t=>{x[t]&&(x[t].dispose(),x[t]=null)})}),(t,e)=>{const l=_("el-button"),u=_("el-option"),m=_("el-select"),r=_("el-form-item"),d=_("el-col"),y=_("el-row"),$=_("el-date-picker"),S=_("el-input-number"),R=_("el-button-group"),B=_("el-form"),g=_("el-card"),W=_("el-divider");return b(),w("div",Ye,[i(g,{class:"control-card",shadow:"never"},{header:a(()=>[s("div",Me,[e[12]||(e[12]=s("div",null,[s("h2",null,"智能体统计报表工作台"),s("p",null,"一键生成基础统计、分析诊断与决策支持报表")],-1)),s("div",He,[i(l,{type:"primary",loading:D.value,onClick:ye},{default:a(()=>[...e[10]||(e[10]=[f("生成可视化报表",-1)])]),_:1},8,["loading"]),i(l,{type:"success",disabled:!p.value,onClick:be},{default:a(()=>[...e[11]||(e[11]=[f("导出HTML报表",-1)])]),_:1},8,["disabled"])])])]),default:a(()=>[i(B,{model:o.value,"label-width":"120px"},{default:a(()=>[i(y,{gutter:16},{default:a(()=>[i(d,{xs:24,md:12},{default:a(()=>[i(r,{label:"聚焦建筑"},{default:a(()=>[i(m,{modelValue:o.value.building_id,"onUpdate:modelValue":e[0]||(e[0]=n=>o.value.building_id=n),placeholder:"可选，默认全部",clearable:"",filterable:""},{default:a(()=>[(b(!0),w(L,null,z(A.value,n=>(b(),ue(u,{key:n.building_id,label:n.building_id,value:n.building_id},null,8,["label","value"]))),128))]),_:1},8,["modelValue"])]),_:1})]),_:1}),i(d,{xs:24,md:12},{default:a(()=>[i(r,{label:"对比建筑"},{default:a(()=>[i(m,{modelValue:o.value.building_ids,"onUpdate:modelValue":e[1]||(e[1]=n=>o.value.building_ids=n),multiple:"",clearable:"",filterable:"",placeholder:"可多选，不选则自动取全部"},{default:a(()=>[(b(!0),w(L,null,z(A.value,n=>(b(),ue(u,{key:n.building_id,label:n.building_id,value:n.building_id},null,8,["label","value"]))),128))]),_:1},8,["modelValue"])]),_:1})]),_:1})]),_:1}),i(y,{gutter:16},{default:a(()=>[i(d,{xs:24,md:12},{default:a(()=>[i(r,{label:"开始时间"},{default:a(()=>[i($,{modelValue:o.value.start_time,"onUpdate:modelValue":e[2]||(e[2]=n=>o.value.start_time=n),type:"datetime","value-format":"YYYY-MM-DD HH:mm:ss",format:"YYYY-MM-DD HH:mm:ss",placeholder:"选择开始时间"},null,8,["modelValue"])]),_:1})]),_:1}),i(d,{xs:24,md:12},{default:a(()=>[i(r,{label:"结束时间"},{default:a(()=>[i($,{modelValue:o.value.end_time,"onUpdate:modelValue":e[3]||(e[3]=n=>o.value.end_time=n),type:"datetime","value-format":"YYYY-MM-DD HH:mm:ss",format:"YYYY-MM-DD HH:mm:ss",placeholder:"选择结束时间"},null,8,["modelValue"])]),_:1})]),_:1})]),_:1}),i(y,{gutter:16},{default:a(()=>[i(d,{xs:24,md:12},{default:a(()=>[i(r,{label:"对比建筑上限"},{default:a(()=>[i(S,{modelValue:o.value.top_n,"onUpdate:modelValue":e[4]||(e[4]=n=>o.value.top_n=n),min:1,max:20},null,8,["modelValue"])]),_:1})]),_:1}),i(d,{xs:24,md:12},{default:a(()=>[i(r,{label:"碳排放因子"},{default:a(()=>[i(S,{modelValue:o.value.carbon_factor,"onUpdate:modelValue":e[5]||(e[5]=n=>o.value.carbon_factor=n),precision:3,step:.01,min:0,max:2},null,8,["modelValue"]),e[13]||(e[13]=s("span",{class:"unit-tip"},"kgCO2/kWh",-1))]),_:1})]),_:1})]),_:1}),i(r,{label:"快速区间"},{default:a(()=>[i(R,null,{default:a(()=>[i(l,{onClick:e[6]||(e[6]=n=>Y("q1"))},{default:a(()=>[...e[14]||(e[14]=[f("2021 Q1",-1)])]),_:1}),i(l,{onClick:e[7]||(e[7]=n=>Y("q2"))},{default:a(()=>[...e[15]||(e[15]=[f("2021 Q2",-1)])]),_:1}),i(l,{onClick:e[8]||(e[8]=n=>Y("summer"))},{default:a(()=>[...e[16]||(e[16]=[f("2021 夏季",-1)])]),_:1}),i(l,{onClick:e[9]||(e[9]=n=>Y("year"))},{default:a(()=>[...e[17]||(e[17]=[f("2021 全年",-1)])]),_:1})]),_:1})]),_:1})]),_:1},8,["model"])]),_:1}),p.value?(b(),w("div",Se,[i(y,{gutter:16,class:"kpi-grid"},{default:a(()=>[i(d,{xs:12,md:6},{default:a(()=>[i(g,{class:"kpi-card",shadow:"hover"},{default:a(()=>[e[18]||(e[18]=s("div",{class:"kpi-label"},"总电耗",-1)),s("div",Le,k(h(p.value.kpis.total_electricity_kwh)),1),e[19]||(e[19]=s("div",{class:"kpi-unit"},"kWh",-1))]),_:1})]),_:1}),i(d,{xs:12,md:6},{default:a(()=>[i(g,{class:"kpi-card",shadow:"hover"},{default:a(()=>[e[20]||(e[20]=s("div",{class:"kpi-label"},"平均COP",-1)),s("div",ze,k(h(p.value.kpis.average_cop,3)),1),e[21]||(e[21]=s("div",{class:"kpi-unit"},"效率指数",-1))]),_:1})]),_:1}),i(d,{xs:12,md:6},{default:a(()=>[i(g,{class:"kpi-card",shadow:"hover"},{default:a(()=>[e[22]||(e[22]=s("div",{class:"kpi-label"},"异常点数",-1)),s("div",Ee,k(p.value.kpis.anomaly_count),1),e[23]||(e[23]=s("div",{class:"kpi-unit"},"个",-1))]),_:1})]),_:1}),i(d,{xs:12,md:6},{default:a(()=>[i(g,{class:"kpi-card",shadow:"hover"},{default:a(()=>[e[24]||(e[24]=s("div",{class:"kpi-label"},"碳排放估算",-1)),s("div",De,k(h(p.value.kpis.carbon_emission_ton,3)),1),e[25]||(e[25]=s("div",{class:"kpi-unit"},"吨CO2",-1))]),_:1})]),_:1})]),_:1}),i(y,{gutter:16,class:"chart-grid"},{default:a(()=>[i(d,{xs:24,lg:12},{default:a(()=>[i(g,{shadow:"never"},{header:a(()=>[...e[26]||(e[26]=[f("月度能耗统计",-1)])]),default:a(()=>[s("div",{ref_key:"monthlyChartRef",ref:N,class:"chart-box"},null,512)]),_:1})]),_:1}),i(d,{xs:24,lg:12},{default:a(()=>[i(g,{shadow:"never"},{header:a(()=>[...e[27]||(e[27]=[f("分建筑能耗对比",-1)])]),default:a(()=>[s("div",{ref_key:"comparisonChartRef",ref:P,class:"chart-box"},null,512)]),_:1})]),_:1}),i(d,{xs:24,lg:12},{default:a(()=>[i(g,{shadow:"never"},{header:a(()=>[...e[28]||(e[28]=[f("异常分布",-1)])]),default:a(()=>[s("div",{ref_key:"anomalyChartRef",ref:U,class:"chart-box"},null,512)]),_:1})]),_:1}),i(d,{xs:24,lg:12},{default:a(()=>[i(g,{shadow:"never"},{header:a(()=>[...e[29]||(e[29]=[f("COP效率趋势",-1)])]),default:a(()=>[s("div",{ref_key:"copChartRef",ref:j,class:"chart-box"},null,512)]),_:1})]),_:1})]),_:1}),i(y,{gutter:16,class:"analysis-grid"},{default:a(()=>[i(d,{xs:24,lg:12},{default:a(()=>[i(g,{shadow:"never"},{header:a(()=>[...e[30]||(e[30]=[f("简要分析结论",-1)])]),default:a(()=>[s("p",Re,k(p.value.analysis.brief),1),s("ul",Be,[(b(!0),w(L,null,z(p.value.analysis.conclusions,(n,O)=>(b(),w("li",{key:`c-${O}`},k(n),1))),128))])]),_:1})]),_:1}),i(d,{xs:24,lg:12},{default:a(()=>[i(g,{shadow:"never"},{header:a(()=>[...e[31]||(e[31]=[f("决策支持建议",-1)])]),default:a(()=>[s("ul",We,[(b(!0),w(L,null,z(p.value.analysis.recommendations,(n,O)=>(b(),w("li",{key:`r-${O}`},k(n),1))),128))]),i(W),s("div",Ne,[e[32]||(e[32]=s("span",null,"潜在节能量:",-1)),s("strong",null,k(h(p.value.decision_support.energy_saving.potential_savings_kwh))+" kWh",1)]),s("div",Pe,[e[33]||(e[33]=s("span",null,"潜在节能率:",-1)),s("strong",null,k(h(p.value.decision_support.energy_saving.potential_savings_pct,2))+"%",1)])]),_:1})]),_:1})]),_:1})])):Ce("",!0)])}}},Te=xe(Ue,[["__scopeId","data-v-2712adc5"]]);export{Te as default};
