const message=document.querySelector('#message');
let games=[];
try { const saved=JSON.parse(localStorage.getItem('games')||'[]'); if(Array.isArray(saved)) games=saved.filter(g=>typeof g.title==='string'&&typeof g.url==='string'&&Array.isArray(g.tags)); } catch {message.textContent='Saved library could not be loaded.';}
function save(){try{localStorage.setItem('games',JSON.stringify(games));}catch{message.textContent='Could not save your library. Storage may be full.';}render();}
function render(){
 const root=document.querySelector('#games');root.replaceChildren();
 games.forEach((game,index)=>{
  if(game.hidden&&!document.querySelector('#show-hidden').checked)return;
  const row=document.createElement('article');row.className='game';
  const name=document.createElement('strong');name.textContent=game.title;row.append(name);
  const tags=document.createElement('span');tags.textContent=game.tags.join(' · ');row.append(tags);
  function button(label,fn){const b=document.createElement('button');b.textContent=label;b.onclick=fn;row.append(b);}
  button(game.tags.includes('slop')?'Unmark slop':'Mark slop',()=>{if(game.tags.includes('slop'))game.tags=game.tags.filter(t=>t!=='slop');else{game.tags.push('slop');game.hidden=true;}save();});
  button(game.hidden?'Restore':'Hide',()=>{game.hidden=!game.hidden;save();});
  button('Remove',()=>{games.splice(index,1);save();});
  root.append(row);
 });
 if(!root.childElementCount){const p=document.createElement('p');p.className='empty';p.textContent='Nothing here yet. Add a game above, or check your hidden games.';root.append(p);}
}
document.querySelector('#add-game').onsubmit=e=>{
 e.preventDefault();const data=new FormData(e.target);const title=data.get('title').trim();
 try{const url=new URL(data.get('url'));if(url.protocol!=='https:'||!['roblox.com','www.roblox.com'].includes(url.hostname)||!/^\/games\/\d+(\/|$)/.test(url.pathname)||!title)throw Error();games.push({title,url:url.href,tags:[],hidden:false});save();e.target.reset();message.textContent='Game saved. Tags filter this launcher’s library only.';}
 catch{message.textContent='Enter a name and a Roblox game link such as https://www.roblox.com/games/123/name.';}
};
document.querySelector('#show-hidden').onchange=render;
document.querySelectorAll('[data-launch]').forEach(button=>button.onclick=async()=>{
 button.disabled=true;message.textContent='Starting…';
 try{const result=await window.lilac.launch(button.dataset.launch);message.textContent=result.ok?'Launch requested. First startup may take a moment.':result.error;}
 catch{message.textContent='Could not contact the launcher.';}finally{button.disabled=false;}
});
window.lilac.onError(text=>{message.textContent=text;});
window.lilac.status().then(status=>{for(const key of ['roblox','studio'])document.querySelector('#'+key+'-status').textContent=status[key]?'● Installed':'○ Not installed — see README';}).catch(()=>{message.textContent='Could not check Flatpak installations.';});
render();
