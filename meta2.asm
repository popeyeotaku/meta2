	adr program
out1    
	tst '*1'
	bf l1
	cl 'gn1'
	out
l1      
	bt l2
	tst '*2'
	bf l3
	cl 'gn2'
	out
l3      
	bt l2
	tst '*'
	bf l4
	cl 'ci'
	out
l4      
	bt l2
	sr
	bf l5
	cl 'cl '
	ci
	out
l5
l2      
	r
output  
	tst '.out'
	bf l6
	tst '('
	be
l7      
	cll out1
	bt l7
	set
	be
	tst ')'
	be
l6      
	bt l8
	tst '.label'
	bf l9
	cl 'lb'
	out
	cll out1
l8
l9      
	bf l10
	cl 'out'
	out
l10     
	r
ex3    
	id
	bf l11
	cl 'cll '
	ci
	out
l11
	bt l12
	sr
	bf l13
	cl 'tst '
	ci
	out
l13
	bt l12
	tst '.id'
	bf l14
	cl 'id'
	out
l14
	bt l12
	tst '.number'
	bf l15
	cl 'num'
	out
l15
	bt l12
	tst '.string'
	bf l16
	cl 'sr'
	out
l16
	bt l12
	tst '('
	bf l17
	cll ex1
	be
	tst ')'
	be
l17
	bt l12
	tst '.empty'
	bf l18
	cl 'set'
	out
l18
	bt l12
	tst '$'
	bf l19
	lb
	gn1
	out
	cll ex3
	be
	cl 'bt '
	gn1
	out
	cl 'set'
	out
l19
l12
	r
ex2     
	cll ex3
	bf l20
	cl 'bf '
	gn1
	out
l20
	bt l21
	cll output
	bf l22
l22
l21
	bf l23
l24
	cll ex3
	bf l25
	cl 'be'
	out
l25
	bt l26 
	cll output
	bf l27
l27
l26
	bt l24
	set
	be
	lb
	gn1
	out
l23
	r
ex1
	cll ex2
	bf l28
l29
	tst '/'
	bf l30
	cl 'bt '
	gn1
	out
	cll ex2
	be
l30
	bt l29
	set
	be
	lb
	gn1
	out
	r
st
	id
	bf l31
	lb
	ci
	out
	tst '='
	be
	cll ex1
	be
	tst '.,'
	be
	cl 'r'
	out
l31
	r
program
	tst '.syntax'
	bf l32
	id
	be
	cl 'adr '
	ci
	out
l33
	cll st
	bt l33
	set
	be
	tst '.end'
	be
	cl 'end'
	out
l32
	end
	r
