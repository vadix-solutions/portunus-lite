dkr="docker-compose -f docker-compose.yml"
$dkr exec django_wsgi pytest \
    --benchmark-only \
    --benchmark-compare --benchmark-autosave \
    --benchmark-compare-fail=median:20% --benchmark-max-time=10 \
    $@
