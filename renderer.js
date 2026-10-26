const message=document.querySelector('#message');
const status=document.querySelector('#results-status');
let library={};let results=[];let cursor=null;let query='';let view='browse';let requestId=0;let loading=false;
const key='lilac-library-v2';
try{
 const saved=JSON.parse(localStorage.getItem(key)||'null');
 if(saved&&typeof saved==='object'&&!Array.isArray(saved))library=saved;
 else {const old=JSON.parse(localStorage.getItem('games')||'[]');for(const game of Array.isArray(old)?old:[]){const match=String(game.url).match(/^https:\/\/(?:www\.)?roblox\.com\/games\/(\d+)/);if(match)library[match[1]]={placeId:match[1],title:String(game.title),saved:true,hidden:!!game.hidden,slop:game.tags?.includes('slop')||false};}}
}catch{message.textContent='Saved library could not be read. Your previous data has not been changed.';}
function persist(){try{localStorage.setItem(key,JSON.stringify(library));}catch{message.textContent='Could not save your filters. Storage may be full.';}render();}
function entry(game){return library[game.placeId]||{};}
function update(game,changes){library[game.placeId]={...game,...entry(game),...changes};persist();}
async function launch(key,placeId,button){button.disabled=true;message.textContent='Starting…';try{const result=await window.lilac.launch(key,placeId);message.textContent=result.ok?'Launch requested. First startup may take a moment.':result.error;}catch{message.textContent='Could not contact the launcher.';}finally{button.disabled=false;}}
function render(){
 const root=document.querySelector('#games');root.replaceChildren();
 const list=view==='browse'?results:Object.values(library).filter(g=>view==='hidden'?g.hidden:g.saved);
 let count=0;
 for(const game of list){
 const state=entry(game);if(view!=='hidden'&&state.hidden&&!document.querySelector('#show-hidden').checked)continue;
 count++;const card=document.createElement('article');card.className='game-card';
 if(game.image){const image=document.createElement('img');image.src=game.image;image.alt='';image.loading='lazy';image.referrerPolicy='no-referrer';image.onerror=()=>image.remove();card.append(image);}
 const title=document.createElement('h4');title.textContent=game.title;card.append(title);
 const info=document.createElement('p');info.textContent=[game.players!==undefined?Number(game.players).toLocaleString()+' playing':null,game.maturity,state.slop?'Marked slop':null,state.hidden?'Hidden':null].filter(Boolean).join(' · ');card.append(info);
 const actions=document.createElement('div');actions.className='card-actions';
 function button(label,fn){const b=document.createElement('button');b.textContent=label;b.onclick=()=>fn(b);actions.append(b);}
 button('Play ↗',b=>launch('roblox',game.placeId,b));
 button(state.saved?'Unsave':'Save',()=>update(game,{saved:!state.saved}));
 button(state.slop?'Unmark slop':'Mark slop',()=>update(game,{slop:!state.slop,...(!state.slop?{hidden:true}:{})}));
 button(state.hidden?'Restore':'Hide',()=>update(game,{hidden:!state.hidden}));
 card.append(actions);root.append(card);
 }
 if(!count){const p=document.createElement('p');p.className='empty';p.textContent=loading?'Searching Roblox…':view==='hidden'?'No hidden games.':view==='saved'?'Save games from Browse, or add a link below.':'No visible games. Try another search, Show hidden, or load more.';root.append(p);}
 document.querySelector('#load-more').hidden=view!=='browse'||!cursor;
 document.querySelector('#load-more').disabled=loading;
 document.querySelector('#search-button').disabled=loading;
 document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
}
async function search(more=false){
 const term=more?query:document.querySelector('#query').value.trim();if(!term)return;
 const id=++requestId;loading=true;view='browse';
 if(!more){query=term;results=[];cursor=null;}
 status.textContent='Searching Roblox…';render();
 try{const response=await window.lilac.search({query:term,cursor:more?cursor:null});if(id!==requestId)return;if(!response.ok)throw Error(response.error);
 const seen=new Set(results.map(g=>g.placeId));results.push(...response.games.filter(g=>!seen.has(g.placeId)));cursor=response.nextPageToken;
 status.textContent=results.length+' results loaded. Your hidden games are filtered on this device.';
 }catch(error){if(id===requestId)status.textContent=error.message||'Search failed. Check your connection and retry.';}
 finally{if(id===requestId){loading=false;render();}}
}
document.querySelector('#search-games').onsubmit=e=>{e.preventDefault();search();};
document.querySelector('#load-more').onclick=()=>search(true);
document.querySelector('#show-hidden').onchange=render;
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{view=b.dataset.view;render();});
document.querySelectorAll('[data-query]').forEach(b=>b.onclick=()=>{document.querySelector('#query').value=b.dataset.query;search();});
document.querySelectorAll('[data-launch]').forEach(b=>b.onclick=()=>launch(b.dataset.launch,undefined,b));
document.querySelector('#add-game').onsubmit=e=>{e.preventDefault();const data=new FormData(e.target);try{const url=new URL(data.get('url'));const match=url.pathname.match(/^\/games\/(\d{1,16})(?:\/|$)/);const title=data.get('title').trim();if(url.protocol!=='https:'||!['roblox.com','www.roblox.com'].includes(url.hostname)||!match||!title)throw Error();update({placeId:match[1],title},{saved:true});view='saved';render();e.target.reset();message.textContent='Game saved.';}catch{message.textContent='Enter a game name and a valid https://www.roblox.com/games/123/name link.';}};
window.lilac.onError(text=>{message.textContent=text;});
window.lilac.status().then(state=>{for(const key of ['roblox','studio'])document.querySelector('#'+key+'-status').textContent=state[key]?'● Installed':'○ Not installed — see README';}).catch(()=>{message.textContent='Could not check Flatpak installations.';});
render();search();

const executorDialog=document.querySelector('#executor-dialog');
const scriptEditor=document.querySelector('#script-editor');
const draftStatus=document.querySelector('#draft-status');
document.querySelector('#open-executor').onclick=()=>{
 try{scriptEditor.value=localStorage.getItem('lilac-script-draft')||'';draftStatus.textContent='';}
 catch{draftStatus.textContent='Could not read the saved draft.';}
 executorDialog.showModal();scriptEditor.focus();
};
document.querySelector('#close-executor').onclick=()=>executorDialog.close();
document.querySelector('#save-script').onclick=()=>{
 try{localStorage.setItem('lilac-script-draft',scriptEditor.value);draftStatus.textContent='Draft saved on this device.';}
 catch{draftStatus.textContent='Could not save the draft. Storage may be full.';}
};

function showPage(page){
 const home=page==='home';
 document.querySelector('#home-page').hidden=!home;
 document.querySelector('#hub-page').hidden=home;
 document.querySelector('#home-tab').setAttribute('aria-pressed',String(home));
 document.querySelector('#hub-tab').setAttribute('aria-pressed',String(!home));
}
document.querySelector('#home-tab').onclick=()=>showPage('home');
document.querySelector('#hub-tab').onclick=()=>showPage('hub');
