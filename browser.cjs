const {randomUUID}=require('node:crypto');
const searchSession=randomUUID();
const APPS={roblox:'org.vinegarhq.Sober',studio:'org.vinegarhq.Vinegar'};
function launchArgs(key,placeId){
 if(!Object.hasOwn(APPS,key))throw Error('Unknown application.');
 const args=['run',APPS[key]];
 if(placeId!==undefined){if(key!=='roblox'||!/^\d{1,16}$/.test(String(placeId))||Number(placeId)<=0)throw Error('Invalid place ID.');args.push('roblox://placeId='+placeId);}
 return args;
}
function normalizeSearch(data){
 if(!Array.isArray(data.searchResults))throw Error('Roblox returned an unexpected search response. Try again later.');
 const seen=new Set();const games=[];
 for(const group of data.searchResults){if(group.contentGroupType!=='Game')continue;for(const item of group.contents||[]){
 const placeId=String(item.rootPlaceId||'');const universeId=String(item.universeId||'');
 if(!/^\d+$/.test(placeId)||!/^\d+$/.test(universeId)||seen.has(universeId))continue;
 seen.add(universeId);games.push({placeId,universeId,title:String(item.name||'Untitled game'),players:Number(item.playerCount)||0,maturity:String(item.ageRecommendationDisplayName||''),image:null});
 }}
 return {games,nextPageToken:typeof data.nextPageToken==='string'?data.nextPageToken:null};
}
async function json(url,fetcher=fetch){
 const response=await fetcher(url,{signal:AbortSignal.timeout(15000),redirect:'error',credentials:'omit'});
 if(!response.ok)throw Error(response.status===429?'Roblox is rate limiting requests. Wait a moment before trying again.':'Roblox request failed ('+response.status+'). Try again later.');
 return response.json();
}
async function searchGames(input,fetcher=fetch){
 if(!input||typeof input.query!=='string'||!input.query.trim()||input.query.length>100||input.cursor&& (typeof input.cursor!=='string'||input.cursor.length>4096))throw Error('Enter a search between 1 and 100 characters.');
 const params=new URLSearchParams({searchQuery:input.query.trim(),pageToken:input.cursor||'',sessionId:searchSession});
 const result=normalizeSearch(await json('https://apis.roblox.com/search-api/omni-search?'+params,fetcher));
 if(result.games.length){try{
 const ids=result.games.map(g=>g.universeId).join(',');
 const thumbs=await json('https://thumbnails.roblox.com/v1/games/icons?'+new URLSearchParams({universeIds:ids,returnPolicy:'PlaceHolder',size:'150x150',format:'Png',isCircular:'false'}),fetcher);
 const images=new Map((thumbs.data||[]).filter(t=>t.state==='Completed').map(t=>[String(t.targetId),t.imageUrl]));
 for(const game of result.games){const value=images.get(game.universeId);if(typeof value==='string'){const url=new URL(value);if(url.protocol==='https:'&&(url.hostname==='rbxcdn.com'||url.hostname.endsWith('.rbxcdn.com')))game.image=url.href;}}
 }catch{/* Search remains useful when thumbnails are unavailable. */}}
 return result;
}
module.exports={launchArgs,normalizeSearch,searchGames};
