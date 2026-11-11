(() => {
  const target=document.getElementById('featured-article');
  if (!target || typeof TTN_ARTICLES === 'undefined') return;
  const now=Date.now();
  const candidates=TTN_ARTICLES.filter(a=>a.id&&a.title&&a.image&&['news','analysis'].includes(a.format)&&Number.isFinite(Date.parse(a.date))&&Date.parse(a.date)<=now).sort((a,b)=>Date.parse(b.date)-Date.parse(a.date));
  const a=candidates[0]; if(!a){target.textContent='No original stories are available right now.';return}
  const url=encodeURIComponent(a.id)+'.html';
  const imageLink=document.createElement('a');imageLink.href=url; const img=document.createElement('img');img.className='featured-img';img.src=a.imageMedium||a.image;img.alt=a.imageAlt||a.title;img.decoding='async';imageLink.append(img);
  const body=document.createElement('div');body.className='featured-body';const meta=document.createElement('div');meta.className='featured-meta';meta.textContent='TTN Finance · '+(window.TTNEditorialMeta?TTNEditorialMeta.format(a.date):a.date.slice(0,10));const h=document.createElement('h2'),link=document.createElement('a');link.href=url;link.textContent=a.title;h.append(link);const desc=document.createElement('p');desc.textContent=a.dek||'';body.append(meta,h,desc);target.replaceChildren(imageLink,body);
  document.addEventListener('DOMContentLoaded',()=>{document.querySelectorAll('.editorial-archive-card').forEach(card=>{const l=card.querySelector('a');if(l&&l.getAttribute('href')===url)card.remove()})});
})();
