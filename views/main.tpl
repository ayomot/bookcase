% rebase("layout.tpl", title="画像")
<div class="show-image">
	<a href="/view/{{name}}/{{mvdict["next"]}}"><img src={{!img}} class="ex-image"></a>
</div>

<div class="operator">
	<a href="/view/{{name}}/{{mvdict["back"]}}"><img src="/img/back.png" class="op-img"/></a>
	<a href="/list/{{name}}/{{mvdict["pagetop"]}}"><img src="/img/top.png" class="op-img"/></a>
	<a href="/view/{{name}}/{{mvdict["next"]}}"><img src="/img/next.png" class="op-img"/></a>
</div>
