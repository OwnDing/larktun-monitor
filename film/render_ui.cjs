const fs=require('fs');const path=require('path');
const {chromium}=require('/Users/ownding/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const ROOT=path.resolve(__dirname,'..');const dir=path.join(ROOT,'out/ui');
const fontCSS=[['Black','900'],['Bold','600 800'],['Regular','100 500']].map(([weight,range])=>`@font-face{font-family:'Noto Sans CJK SC';src:url(data:font/otf;base64,${fs.readFileSync(path.join(ROOT,'assets/fonts/NotoSansCJKsc-'+weight+'.otf')).toString('base64')});font-weight:${range}}`).join('');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--force-color-profile=srgb','--font-render-hinting=none']});
 const page=await browser.newPage({viewport:{width:1080,height:2200},deviceScaleFactor:1});
 for (const shot of ['S05','S10','PAYMENT','S14_bird_original']) {
  const bird=shot.startsWith('S14');await page.setViewportSize({width:1080,height:bird?1920:2200});
  let svg=fs.readFileSync(path.join(dir,shot+'.svg'),'utf8').replace(/ns0:/g,'').replace(/xmlns:ns0=/g,'xmlns=');
  await page.setContent(`<style>${fontCSS}html,body{margin:0;padding:0;background:transparent}svg{display:block}text{font-family:'Noto Sans CJK SC'!important}</style>${svg}`);
  await page.evaluate(()=>document.fonts.ready);
  const out=path.join(dir,'frames',shot);fs.mkdirSync(out,{recursive:true});
  const count=bird||shot==='PAYMENT'?1:90;
  for(let f=0;f<count;f++) {
   await page.evaluate(({shot,f})=>{
    const clamp=t=>Math.max(0,Math.min(1,t));
    if(shot==='S05'){
     const q=clamp((f-12)/6), p=clamp((f-36)/12),t=clamp((f-60)/20);
     document.getElementById('timeline').setAttribute('opacity',String(1-.65*q));
     const lock=document.getElementById('lock');lock.setAttribute('opacity',String(q));lock.setAttribute('transform',`translate(0,${-25*(1-q)})`);
     const shake=f>=60&&f<76?Math.sin((f-60)*1.4)*7*(1-(f-60)/16):0;
     document.getElementById('paywall').setAttribute('transform',`translate(${shake},${320*(1-p)**3})`);document.getElementById('paywall').setAttribute('opacity',String(p));
     const ripple=document.getElementById('ripple');ripple.setAttribute('r',String(6+90*t));ripple.setAttribute('opacity',String(f>=60?.8*(1-t):0));
    }else if(shot==='S10'){
     const q=Math.max(.0001,clamp(f/15));document.getElementById('livecard').setAttribute('transform',`translate(${18+138*(1-q)},${366+98*(1-q)}) scale(${q})`);
     document.getElementById('latency').textContent=f<15?'正在连接 · 延迟 --':'已连接 · 延迟 18ms';
    }
   },{shot,f});
   await page.screenshot({path:path.join(out,String(f+1).padStart(4,'0')+'.png'),omitBackground:true});
  }
  console.log('UI rendered',shot,count);
 }
 await browser.close();
})();
