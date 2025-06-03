# 🧪 Smart Grid Table Test Guide

Deze gids legt uit hoe je alle tests kunt uitvoeren voor de gerefactorde Smart Grid Table applicatie.

## 📋 Test Overzicht

We hebben een uitgebreide test suite met verschillende niveaus van testing:

### 🏗️ Test Categorieën

1. **Original Unit Tests** - Bestaande tests voor binary encoding en model segmentation
2. **Pandapower Tests** - Tests voor de Pandapower implementatie en netwerk functionaliteit  
3. **Integration Tests** - Tests voor de gerefactorde modules (AppState, ConfigLoader, MQTTManager, CommandDispatcher)
4. **Comprehensive Tests** - Uitgebreide tests voor error handling, edge cases, en performance
5. **Application Smoke Test** - Basis test voor applicatie startup en imports
6. **PyTest Discovery** - Automatische test discovery

## 🚀 Snelstart

### Alle tests uitvoeren (aanbevolen):
```bash
make test-all
# OF
python run_all_tests.py
```

### Snelle tests (origineel + integration):
```bash
make test-quick
```

### Individuele test categorieën:
```bash
make test-original       # Originele unit tests
make test-pandapower     # Pandapower tests  
make test-integration    # Integration tests
make test-comprehensive  # Comprehensive tests
make test-app           # Applicatie smoke test
```

## 🔧 Makefile Commando's

| Commando | Beschrijving |
|----------|-------------|
| `make help` | Toont alle beschikbare commando's |
| `make test-all` | Volledige test pipeline |
| `make test-quick` | Snelle tests (origineel + integration) |
| `make test-original` | Originele unit tests |
| `make test-pandapower` | Pandapower implementatie tests |
| `make test-integration` | Integration tests voor gerefactorde modules |
| `make test-comprehensive` | Uitgebreide tests (error handling, edge cases) |
| `make test-app` | Applicatie smoke test |
| `make test-pytest` | PyTest discovery |
| `make clean` | Cache files opruimen |

## 🤖 GitHub Actions CI/CD

De tests worden automatisch uitgevoerd bij:
- Push naar `main` branch
- Push naar `feature/pandapower` branch  
- Pull requests naar deze branches

De GitHub Actions workflow bevindt zich in `.github/workflows/python-ci.yml` en voert uit:
1. Linting met flake8
2. Alle test categorieën in volgorde
3. Test rapportage

## 📊 Test Resultaten Interpreteren

### ✅ Succesvol
```
🎉 ALL TESTS PASSED! The refactored application is ready!
```

### ❌ Failed
```
⚠️ Some tests failed. Please review the results above.
```

### 📈 Test Metrics
De pipeline toont:
- Total Duration: Totale uitvoeringstijd
- Success Rate: Percentage geslaagde tests
- Detailed Breakdown: Per categorie resultaten

## 🐛 Troubleshooting

### Veelvoorkomende problemen:

1. **MQTT Connection Errors**: Normaal in simulation mode zonder broker
2. **Import Errors**: Zorg dat je in de juiste directory staat
3. **Permission Errors**: Controleer file permissions
4. **Cache Issues**: Run `make clean` om cache te legen

### Debug tips:

```bash
# Verbose output
python -m pytest test/ -v -s

# Specifieke test
python test/test_refactored_comprehensive.py

# Met coverage
python -m pytest test/ --cov=. --cov-report=html
```

## 📁 Test Bestanden

```
├── test/
│   ├── run_tests.py                     # Originele test runner
│   ├── test_pandapower_implementation.py # Pandapower tests
│   ├── test_refactored_comprehensive.py  # Comprehensive tests
│   ├── binary_decoder_test.py           # Binary encoding tests
│   ├── binary_encoder_test.py           # Binary encoding tests
│   └── model_segmentation_test.py       # Model segmentation tests
├── test_refactored_app.py               # Integration tests (root)
├── run_all_tests.py                     # Lokale test pipeline
├── Makefile                             # Test commando's
└── .github/workflows/python-ci.yml     # GitHub Actions
```

## 🎯 Test Coverage

Onze tests dekken:

### AppState Module
- ✅ Mode validatie en state management
- ✅ Error handling voor invalid inputs
- ✅ State transitions
- ✅ Force update mechanisme

### ConfigLoader Module  
- ✅ JSON parsing en error handling
- ✅ Missing file handling
- ✅ GUI remap loading
- ✅ Configuration value retrieval

### MQTTManager Module
- ✅ Connection management
- ✅ Message handling en filtering
- ✅ Simulation mode overrides
- ✅ Error recovery

### CommandDispatcher Module
- ✅ Command parsing en dispatch
- ✅ UI message handling
- ✅ Invalid command handling
- ✅ All command categories

### Integration
- ✅ Full system initialization
- ✅ Error recovery scenarios
- ✅ Performance under load

## 🚀 Volgende Stappen

1. **Run alle tests**: `make test-all`
2. **Controleer CI/CD**: Push naar GitHub en bekijk Actions
3. **Monitor coverage**: Voeg coverage reporting toe indien gewenst
4. **Extend tests**: Voeg tests toe voor nieuwe features

## 💡 Tips

- Gebruik `make test-quick` voor dagelijkse development
- Run `make test-all` voor volledige validatie
- GitHub Actions geeft automatische feedback op PRs
- Tests zijn ontworpen om snel en betrouwbaar te zijn

---

✨ **Happy Testing!** De gerefactorde Smart Grid Table applicatie is nu volledig getest en klaar voor productie gebruik. 