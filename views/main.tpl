% rebase("layout.tpl", title="画像")
<div class="show-image">
	<a href = {{mvdict["next"]}}><img src={{!img}} class="ex-image"></a>
</div>

<div class="operator">
	<a href = {{mvdict["back"]}}><img src="/img/back.png" class="op-img"/></a>
	<a href = {{mvdict["pagetop"]}}><img src="/img/top.png" class="op-img"/></a>
	<a href = {{mvdict["next"]}}><img src="/img/next.png" class="op-img"/></a>
</div>
