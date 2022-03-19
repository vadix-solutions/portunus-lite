dkr="docker-compose -f docker-compose.yml"
cov="${COV_TEST---cov=.}"
$dkr exec django_wsgi pytest \
    -s $cov --benchmark-skip \
    $@
